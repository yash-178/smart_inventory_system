"""
alerts.py
---------
Low-stock / out-of-stock alert detection and summary statistics.
"""

import pandas as pd


def get_alerts(inventory: pd.DataFrame) -> dict:
    low_stock = inventory[inventory["status"] == "Low Stock"].copy()
    out_of_stock = inventory[inventory["status"] == "Out of Stock"].copy()

    low_stock = low_stock.sort_values("stock_quantity")
    out_of_stock = out_of_stock.sort_values("inventory_value", ascending=False)

    cols = ["product_id", "product_name", "category", "supplier",
            "stock_quantity", "reorder_level", "unit_price", "inventory_value",
            "lead_time_days"]
    cols = [c for c in cols if c in inventory.columns]

    return {
        "low_stock_count": int(len(low_stock)),
        "out_of_stock_count": int(len(out_of_stock)),
        "low_stock_items": low_stock[cols].to_dict(orient="records"),
        "out_of_stock_items": out_of_stock[cols].to_dict(orient="records"),
        "potential_lost_value": round(float(out_of_stock["inventory_value"].sum()
                                             + (out_of_stock["reorder_level"] * out_of_stock["unit_price"]).sum()), 2),
    }
