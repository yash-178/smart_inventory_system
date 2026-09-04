"""
insights.py
------------
Business insights derived from combining inventory levels with historical
sales velocity:
  - fast_moving   : high average daily sales velocity
  - slow_moving    : low velocity but still holding stock
  - overstocked   : current stock represents far more "days of supply"
                    than is reasonable given the recent sales pace
  - restocking recommendations : products likely to run out before the
                    supplier lead time elapses, given recent velocity
"""

import numpy as np
import pandas as pd

OVERSTOCK_DAYS_THRESHOLD = 90   # more than ~3 months of stock at current pace
SLOW_MOVING_DAYS_THRESHOLD = 60  # more than ~2 months of stock and low velocity
VELOCITY_WINDOW_DAYS = 30


def _sales_velocity(sales: pd.DataFrame, window_days=VELOCITY_WINDOW_DAYS) -> pd.DataFrame:
    if sales.empty:
        return pd.DataFrame(columns=["product_id", "avg_daily_sales", "total_units_sold"])

    max_date = sales["date"].max()
    cutoff = max_date - pd.Timedelta(days=window_days)
    recent = sales[sales["date"] >= cutoff]

    grouped = recent.groupby("product_id")["quantity_sold"].sum().reset_index()
    grouped.columns = ["product_id", "total_units_sold"]
    # normalize by the actual number of days observed in the window
    n_days = max(1, (max_date - cutoff).days)
    grouped["avg_daily_sales"] = (grouped["total_units_sold"] / n_days).round(3)
    return grouped


def generate_insights(inventory: pd.DataFrame, sales: pd.DataFrame) -> dict:
    velocity = _sales_velocity(sales)
    merged = inventory.merge(velocity, on="product_id", how="left")
    merged["avg_daily_sales"] = merged["avg_daily_sales"].fillna(0)
    merged["total_units_sold"] = merged["total_units_sold"].fillna(0)

    # Days of supply = how many days current stock would last at recent pace
    merged["days_of_supply"] = np.where(
        merged["avg_daily_sales"] > 0,
        merged["stock_quantity"] / merged["avg_daily_sales"],
        np.inf,
    )

    velocity_75 = merged["avg_daily_sales"].quantile(0.75)
    velocity_25 = merged.loc[merged["avg_daily_sales"] > 0, "avg_daily_sales"].quantile(0.25) \
        if (merged["avg_daily_sales"] > 0).any() else 0

    fast_moving = merged[merged["avg_daily_sales"] >= max(velocity_75, 0.01)].copy()
    fast_moving = fast_moving.sort_values("avg_daily_sales", ascending=False)

    slow_moving = merged[
        (merged["avg_daily_sales"] > 0)
        & (merged["avg_daily_sales"] <= velocity_25)
        & (merged["stock_quantity"] > 0)
    ].copy()
    slow_moving = slow_moving.sort_values("avg_daily_sales")

    never_sold = merged[(merged["total_units_sold"] == 0) & (merged["stock_quantity"] > 0)].copy()

    overstocked = merged[
        (merged["days_of_supply"] > OVERSTOCK_DAYS_THRESHOLD) & (merged["stock_quantity"] > 0)
        & (merged["avg_daily_sales"] > 0)
    ].copy()
    overstocked = overstocked.sort_values("days_of_supply", ascending=False)

    # Restocking recommendations: items likely to stock out before lead time
    merged["projected_stockout_days"] = merged["days_of_supply"]
    at_risk = merged[
        (merged["avg_daily_sales"] > 0)
        & (merged["projected_stockout_days"] <= merged["lead_time_days"])
        & (merged["status"] != "Out of Stock")
    ].copy()
    at_risk["recommended_reorder_qty"] = (
        (merged["avg_daily_sales"] * (merged["lead_time_days"] + 30)) - merged["stock_quantity"]
    ).clip(lower=0).round().astype(int)
    at_risk = at_risk.sort_values("projected_stockout_days")

    def _records(df, cols):
        cols = [c for c in cols if c in df.columns]
        out = df[cols].replace([np.inf, -np.inf], None)
        return out.to_dict(orient="records")

    base_cols = ["product_id", "product_name", "category", "supplier",
                 "stock_quantity", "avg_daily_sales", "total_units_sold", "days_of_supply"]

    return {
        "fast_moving": _records(fast_moving.head(15), base_cols),
        "slow_moving": _records(slow_moving.head(15), base_cols),
        "never_sold": _records(never_sold.head(15), base_cols[:7]),
        "overstocked": _records(overstocked.head(15), base_cols + ["inventory_value"]),
        "restock_recommendations": _records(
            at_risk.head(20),
            ["product_id", "product_name", "category", "supplier", "stock_quantity",
             "reorder_level", "lead_time_days", "avg_daily_sales",
             "projected_stockout_days", "recommended_reorder_qty"],
        ),
        "summary": {
            "fast_moving_count": int(len(fast_moving)),
            "slow_moving_count": int(len(slow_moving)),
            "never_sold_count": int(len(never_sold)),
            "overstocked_count": int(len(overstocked)),
            "restock_needed_count": int(len(at_risk)),
            "overstocked_value_tied_up": round(float(overstocked["inventory_value"].sum()), 2),
        },
    }
