"""
analytics.py
------------
Aggregation functions used by the Dashboard and Analytics pages. Every
function returns plain Python dict/list structures that are JSON-safe,
ready to be handed straight to Plotly.js on the frontend.
"""

import numpy as np
import pandas as pd


def dashboard_summary(inventory: pd.DataFrame) -> dict:
    total_products = int(len(inventory))
    total_categories = int(inventory["category"].nunique())
    total_stock_units = int(inventory["stock_quantity"].sum())
    low_stock = int((inventory["status"] == "Low Stock").sum())
    out_of_stock = int((inventory["status"] == "Out of Stock").sum())
    in_stock = int((inventory["status"] == "In Stock").sum())
    total_inventory_value = round(float(inventory["inventory_value"].sum()), 2)
    avg_unit_price = round(float(inventory["unit_price"].mean()), 2) if total_products else 0.0
    total_suppliers = int(inventory["supplier"].nunique())

    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_suppliers": total_suppliers,
        "total_stock_units": total_stock_units,
        "in_stock_count": in_stock,
        "low_stock_count": low_stock,
        "out_of_stock_count": out_of_stock,
        "total_inventory_value": total_inventory_value,
        "avg_unit_price": avg_unit_price,
    }


def category_stock_distribution(inventory: pd.DataFrame) -> dict:
    grouped = (
        inventory.groupby("category")
        .agg(total_stock=("stock_quantity", "sum"),
             product_count=("product_id", "count"),
             total_value=("inventory_value", "sum"))
        .reset_index()
        .sort_values("total_stock", ascending=False)
    )
    return {
        "categories": grouped["category"].tolist(),
        "total_stock": grouped["total_stock"].astype(int).tolist(),
        "product_count": grouped["product_count"].astype(int).tolist(),
        "total_value": grouped["total_value"].round(2).tolist(),
    }


def top_products_by_stock(inventory: pd.DataFrame, n=10) -> dict:
    top = inventory.sort_values("stock_quantity", ascending=False).head(n)
    return {
        "product_names": top["product_name"].tolist(),
        "stock_quantity": top["stock_quantity"].astype(int).tolist(),
        "category": top["category"].tolist(),
    }


def monthly_sales_trend(sales: pd.DataFrame) -> dict:
    if sales.empty:
        return {"months": [], "units_sold": [], "revenue": []}
    grouped = (
        sales.groupby("month")
        .agg(units_sold=("quantity_sold", "sum"), revenue=("revenue", "sum"))
        .reset_index()
        .sort_values("month")
    )
    return {
        "months": grouped["month"].tolist(),
        "units_sold": grouped["units_sold"].astype(int).tolist(),
        "revenue": grouped["revenue"].round(2).tolist(),
    }


def inventory_value_by_category(inventory: pd.DataFrame) -> dict:
    grouped = (
        inventory.groupby("category")["inventory_value"]
        .sum()
        .reset_index()
        .sort_values("inventory_value", ascending=False)
    )
    return {
        "categories": grouped["category"].tolist(),
        "inventory_value": grouped["inventory_value"].round(2).tolist(),
    }


def supplier_performance(inventory: pd.DataFrame, sales: pd.DataFrame) -> dict:
    """Combines inventory-side metrics (lead time, stockout rate) with
    sales-side metrics (revenue generated) per supplier."""
    inv_grouped = (
        inventory.groupby("supplier")
        .agg(
            product_count=("product_id", "count"),
            avg_lead_time_days=("lead_time_days", "mean"),
            total_inventory_value=("inventory_value", "sum"),
            out_of_stock_count=("status", lambda s: (s == "Out of Stock").sum()),
        )
        .reset_index()
    )

    merged = inventory[["product_id", "supplier"]].merge(sales, on="product_id", how="right")
    rev_grouped = merged.groupby("supplier")["revenue"].sum().reset_index()
    rev_grouped.columns = ["supplier", "total_revenue"]

    result = inv_grouped.merge(rev_grouped, on="supplier", how="left")
    result["total_revenue"] = result["total_revenue"].fillna(0)
    result["stockout_rate"] = (
        result["out_of_stock_count"] / result["product_count"].replace(0, np.nan)
    ).fillna(0).round(3)
    result = result.sort_values("total_revenue", ascending=False)

    return {
        "suppliers": result["supplier"].tolist(),
        "product_count": result["product_count"].astype(int).tolist(),
        "avg_lead_time_days": result["avg_lead_time_days"].round(1).tolist(),
        "total_inventory_value": result["total_inventory_value"].round(2).tolist(),
        "total_revenue": result["total_revenue"].round(2).tolist(),
        "stockout_rate": result["stockout_rate"].tolist(),
    }


def top_selling_products(inventory: pd.DataFrame, sales: pd.DataFrame, n=10) -> dict:
    if sales.empty:
        return {"product_names": [], "units_sold": [], "revenue": []}
    grouped = sales.groupby("product_id").agg(
        units_sold=("quantity_sold", "sum"), revenue=("revenue", "sum")
    ).reset_index()
    merged = grouped.merge(inventory[["product_id", "product_name", "category"]], on="product_id", how="left")
    merged["product_name"] = merged["product_name"].fillna(merged["product_id"])
    merged = merged.sort_values("units_sold", ascending=False).head(n)
    return {
        "product_names": merged["product_name"].tolist(),
        "units_sold": merged["units_sold"].astype(int).tolist(),
        "revenue": merged["revenue"].round(2).tolist(),
        "category": merged["category"].fillna("Uncategorized").tolist(),
    }


def status_breakdown(inventory: pd.DataFrame) -> dict:
    counts = inventory["status"].value_counts()
    order = ["In Stock", "Low Stock", "Out of Stock"]
    return {
        "labels": order,
        "values": [int(counts.get(label, 0)) for label in order],
    }
