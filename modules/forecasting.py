"""
forecasting.py
---------------
Demand forecasting for individual products or whole categories.

Supported methods:
  - moving_average : simple rolling-average projection (robust baseline)
  - linear_regression : sklearn LinearRegression on day-index trend
  - random_forest : sklearn RandomForestRegressor using lag + calendar features

All methods operate on a daily time series aggregated from the sales
transactions and return both the historical series (for charting) and the
forecast for the requested horizon, plus a simple recommended-reorder
quantity based on the forecast vs. current stock and supplier lead time.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

MIN_HISTORY_DAYS = 10


class ForecastError(Exception):
    pass


def _build_daily_series(sales: pd.DataFrame, product_id=None, category=None,
                         inventory: pd.DataFrame = None) -> pd.Series:
    if product_id:
        subset = sales[sales["product_id"] == product_id]
    elif category and inventory is not None:
        product_ids = inventory.loc[inventory["category"] == category, "product_id"]
        subset = sales[sales["product_id"].isin(product_ids)]
    else:
        subset = sales

    if subset.empty:
        return pd.Series(dtype=float)

    daily = subset.groupby("date")["quantity_sold"].sum()
    full_range = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full_range, fill_value=0)
    return daily


def _moving_average_forecast(series: pd.Series, periods: int, window: int = 7):
    window = min(window, len(series))
    avg = float(series.tail(window).mean())
    last_date = series.index.max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=periods, freq="D")
    forecast_values = [round(avg, 2)] * periods
    return future_dates, forecast_values


def _linear_regression_forecast(series: pd.Series, periods: int):
    x = np.arange(len(series)).reshape(-1, 1)
    y = series.values
    model = LinearRegression()
    model.fit(x, y)

    future_x = np.arange(len(series), len(series) + periods).reshape(-1, 1)
    preds = model.predict(future_x)
    preds = np.clip(preds, 0, None)

    last_date = series.index.max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=periods, freq="D")
    return future_dates, [round(float(v), 2) for v in preds], model


def _make_lag_features(series: pd.Series, lags=(1, 2, 3, 7, 14)):
    df = pd.DataFrame({"y": series.values}, index=series.index)
    for lag in lags:
        df[f"lag_{lag}"] = df["y"].shift(lag)
    df["dayofweek"] = df.index.dayofweek
    df["day_index"] = np.arange(len(df))
    df = df.dropna()
    return df, lags


def _random_forest_forecast(series: pd.Series, periods: int):
    df, lags = _make_lag_features(series)
    if len(df) < 15:
        raise ForecastError("Not enough history for Random Forest (need 15+ usable days).")

    feature_cols = [f"lag_{lag}" for lag in lags] + ["dayofweek", "day_index"]
    model = RandomForestRegressor(n_estimators=200, max_depth=6, random_state=42)
    model.fit(df[feature_cols], df["y"])

    history = list(series.values)
    last_date = series.index.max()
    day_index = len(series)
    forecast_values = []
    future_dates = []

    for step in range(periods):
        next_date = last_date + pd.Timedelta(days=step + 1)
        row = {}
        for lag in lags:
            row[f"lag_{lag}"] = history[-lag] if len(history) >= lag else 0
        row["dayofweek"] = next_date.dayofweek
        row["day_index"] = day_index
        x_row = pd.DataFrame([row])[feature_cols]
        pred = max(0.0, float(model.predict(x_row)[0]))
        forecast_values.append(round(pred, 2))
        history.append(pred)
        future_dates.append(next_date)
        day_index += 1

    return future_dates, forecast_values, model


def generate_forecast(sales: pd.DataFrame, inventory: pd.DataFrame,
                       product_id=None, category=None,
                       method="linear_regression", periods=30) -> dict:
    """Main entry point used by the API layer.

    Returns a dict with historical + forecast series, chosen method (with
    automatic fallback if data is insufficient), and a reorder recommendation.
    """
    if not product_id and not category:
        raise ForecastError("Either product_id or category must be provided.")
    if periods <= 0 or periods > 180:
        raise ForecastError("periods must be between 1 and 180.")

    series = _build_daily_series(sales, product_id=product_id, category=category, inventory=inventory)

    if series.empty or len(series) < MIN_HISTORY_DAYS:
        raise ForecastError(
            f"Not enough sales history to forecast (need at least {MIN_HISTORY_DAYS} days of data)."
        )

    fallback_used = False
    requested_method = method

    if method == "moving_average":
        future_dates, forecast_values = _moving_average_forecast(series, periods)
    elif method == "linear_regression":
        future_dates, forecast_values, _ = _linear_regression_forecast(series, periods)
    elif method == "random_forest":
        try:
            future_dates, forecast_values, _ = _random_forest_forecast(series, periods)
        except ForecastError:
            # graceful fallback to a method that needs less data
            future_dates, forecast_values, _ = _linear_regression_forecast(series, periods)
            fallback_used = True
            method = "linear_regression"
    else:
        raise ForecastError(f"Unknown forecasting method: {method}")

    total_forecast_demand = round(float(sum(forecast_values)), 2)
    avg_daily_forecast = round(total_forecast_demand / periods, 2) if periods else 0.0

    # Reorder recommendation (only meaningful for a single product)
    recommendation = None
    if product_id is not None:
        prod_rows = inventory[inventory["product_id"] == product_id]
        if not prod_rows.empty:
            prod = prod_rows.iloc[0]
            lead_time = int(prod.get("lead_time_days", 7) or 7)
            demand_during_lead_time = avg_daily_forecast * lead_time
            current_stock = int(prod["stock_quantity"])
            reorder_level = int(prod["reorder_level"])
            projected_shortfall = max(0.0, demand_during_lead_time + reorder_level - current_stock)
            recommendation = {
                "current_stock": current_stock,
                "lead_time_days": lead_time,
                "projected_demand_during_lead_time": round(demand_during_lead_time, 2),
                "recommended_reorder_qty": int(round(projected_shortfall)),
                "action_needed": bool(projected_shortfall > 0),
            }

    return {
        "method_used": method,
        "requested_method": requested_method,
        "fallback_used": fallback_used,
        "history_dates": [d.strftime("%Y-%m-%d") for d in series.index],
        "history_values": [round(float(v), 2) for v in series.values],
        "forecast_dates": [d.strftime("%Y-%m-%d") for d in future_dates],
        "forecast_values": forecast_values,
        "total_forecast_demand": total_forecast_demand,
        "avg_daily_forecast": avg_daily_forecast,
        "recommendation": recommendation,
    }
