"""
cleaning.py
-----------
Data cleaning utilities for the inventory and sales datasets.

Each cleaning function returns a tuple of (cleaned_dataframe, report_dict)
so the app can surface a transparent "data quality report" to the user
(useful both for debugging and for demonstrating the cleaning step of the
internship task).
"""

import numpy as np
import pandas as pd

VALID_CATEGORIES = {
    "Electronics", "Groceries", "Furniture", "Apparel",
    "Stationery", "Toys", "Sports", "Home & Kitchen",
}


def _to_numeric_currency(series):
    """Convert a column that may contain plain numbers or strings like
    'Rs.1234.5' into a clean numeric series."""
    cleaned = (
        series.astype(str)
        .str.replace(r"[^\d.\-]", "", regex=True)
        .replace("", np.nan)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def clean_inventory_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the raw inventory dataframe.

    Steps:
      1. Standardize column presence / strip whitespace from text fields
      2. Coerce numeric columns (handles currency-formatted strings)
      3. Standardize category & supplier text casing
      4. Parse mixed-format dates
      5. Fill missing values sensibly (median for numeric, 'Unknown' for text)
      6. Drop duplicate product_id rows (keep most recent)
      7. Validate & fix invalid values (negative stock, zero/negative prices)
    """
    report = {"steps": [], "rows_before": len(df)}
    df = df.copy()

    required_cols = ["product_id", "product_name", "category", "supplier",
                      "stock_quantity", "reorder_level", "unit_price"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Inventory data is missing required columns: {missing_cols}")

    # 1. Strip whitespace on text columns
    text_cols = ["product_id", "product_name", "category", "supplier"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df.loc[df[col].isin(["nan", "None", ""]), col] = np.nan

    # 2. Coerce numeric columns (unit_price may contain "Rs.1234.5")
    numeric_cols = ["stock_quantity", "reorder_level", "unit_cost", "lead_time_days"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "unit_price" in df.columns:
        df["unit_price"] = _to_numeric_currency(df["unit_price"])

    # 3. Standardize category & supplier casing (title case)
    if "category" in df.columns:
        df["category"] = df["category"].str.title()
        # fix categories that don't match known set (fuzzy: strip stray spaces)
        unknown_cats = df.loc[~df["category"].isin(VALID_CATEGORIES) & df["category"].notna(), "category"]
        report["unrecognized_categories"] = sorted(unknown_cats.unique().tolist())
    if "supplier" in df.columns:
        df["supplier"] = df["supplier"].str.title()

    # 4. Parse mixed-format dates (handles YYYY-MM-DD and DD/MM/YYYY)
    for col in ["date_added", "last_restocked_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=False, format="mixed")

    # 5. Missing value handling
    n_missing_before = int(df[required_cols].isna().sum().sum())

    if "category" in df.columns:
        df["category"] = df["category"].fillna("Uncategorized")
    if "supplier" in df.columns:
        df["supplier"] = df["supplier"].fillna("Unknown Supplier")
    if "product_name" in df.columns:
        df["product_name"] = df["product_name"].fillna("Unnamed Product")

    if "unit_price" in df.columns:
        cat_median_price = df.groupby("category")["unit_price"].transform("median")
        df["unit_price"] = df["unit_price"].fillna(cat_median_price)
        df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())
    if "unit_cost" in df.columns:
        df["unit_cost"] = df["unit_cost"].fillna(df["unit_price"] * 0.65)
    if "stock_quantity" in df.columns:
        df["stock_quantity"] = df["stock_quantity"].fillna(0)
    if "reorder_level" in df.columns:
        df["reorder_level"] = df["reorder_level"].fillna(
            (df["stock_quantity"] * 0.2).round().clip(lower=5)
        )
    if "lead_time_days" in df.columns:
        df["lead_time_days"] = df["lead_time_days"].fillna(df["lead_time_days"].median())

    n_missing_after_fill = int(df[required_cols].isna().sum().sum())
    report["missing_values_filled"] = n_missing_before - n_missing_after_fill

    # Drop rows still missing a critical identifier (can't be recovered)
    before = len(df)
    df = df.dropna(subset=["product_id"])
    report["rows_dropped_missing_id"] = before - len(df)

    # 6. Duplicates - keep the last occurrence (assumed most recent update)
    before = len(df)
    df = df.drop_duplicates(subset=["product_id"], keep="last")
    report["duplicate_rows_removed"] = before - len(df)

    # 7. Validation & correction of invalid values
    invalid_stock = int((df["stock_quantity"] < 0).sum())
    df["stock_quantity"] = df["stock_quantity"].clip(lower=0)
    report["negative_stock_corrected"] = invalid_stock

    invalid_price = int((df["unit_price"] <= 0).sum())
    fallback_price = df.loc[df["unit_price"] > 0, "unit_price"].median()
    df.loc[df["unit_price"] <= 0, "unit_price"] = fallback_price if pd.notna(fallback_price) else 1.0
    report["invalid_price_corrected"] = invalid_price

    df["reorder_level"] = df["reorder_level"].clip(lower=0)
    df["stock_quantity"] = df["stock_quantity"].round().astype(int)
    df["reorder_level"] = df["reorder_level"].round().astype(int)
    df["unit_price"] = df["unit_price"].round(2)
    df["unit_cost"] = df["unit_cost"].round(2)
    if "lead_time_days" in df.columns:
        df["lead_time_days"] = df["lead_time_days"].clip(lower=1).round().astype(int)

    # Derived fields
    df["inventory_value"] = (df["stock_quantity"] * df["unit_price"]).round(2)

    def _status(row):
        if row["stock_quantity"] <= 0:
            return "Out of Stock"
        elif row["stock_quantity"] <= row["reorder_level"]:
            return "Low Stock"
        return "In Stock"

    df["status"] = df.apply(_status, axis=1)

    report["rows_after"] = len(df)
    df = df.reset_index(drop=True)
    return df, report


def clean_sales_data(df: pd.DataFrame, valid_product_ids=None) -> tuple[pd.DataFrame, dict]:
    """Clean the raw sales/transactions dataframe.

    Steps: parse dates, coerce numerics, drop duplicates, fill/derive
    missing revenue, and drop rows referencing unknown products.
    """
    report = {"rows_before": len(df)}
    df = df.copy()

    required_cols = ["date", "product_id", "quantity_sold"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Sales data is missing required columns: {missing_cols}")

    df["product_id"] = df["product_id"].astype(str).str.strip()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce")
    if "revenue" in df.columns:
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["date", "product_id"])
    report["rows_dropped_missing_key_fields"] = before - len(df)

    before = len(df)
    df = df.drop_duplicates()
    report["duplicate_rows_removed"] = before - len(df)

    df["quantity_sold"] = df["quantity_sold"].fillna(0).clip(lower=0).round().astype(int)

    if "revenue" in df.columns:
        n_missing_rev = int(df["revenue"].isna().sum())
        df["revenue"] = df["revenue"].fillna(0.0).clip(lower=0)
        report["missing_revenue_filled"] = n_missing_rev
    else:
        df["revenue"] = 0.0

    if valid_product_ids is not None:
        before = len(df)
        df = df[df["product_id"].isin(valid_product_ids)]
        report["rows_dropped_unknown_product"] = before - len(df)

    df["month"] = df["date"].dt.to_period("M").astype(str)
    report["rows_after"] = len(df)
    df = df.reset_index(drop=True)
    return df, report
