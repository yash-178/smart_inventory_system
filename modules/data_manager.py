"""
data_manager.py
----------------
Single source of truth for loading and caching the cleaned inventory and
sales datasets. Uses a simple in-memory cache (module-level singleton) so
the CSVs are read + cleaned once per process, with a manual reload()
option exposed via the API for demo purposes.
"""

import os
import threading
import pandas as pd

from modules.cleaning import clean_inventory_data, clean_sales_data
from generate_data import (
    ensure_data_exists,
    INVENTORY_RAW_PATH,
    SALES_RAW_PATH,
)

_lock = threading.Lock()

_cache = {
    "inventory": None,
    "sales": None,
    "inventory_report": None,
    "sales_report": None,
    "loaded": False,
}


class DataLoadError(Exception):
    """Raised when the underlying CSV files can't be read or parsed."""
    pass


def _load_from_disk():
    ensure_data_exists()

    if not os.path.exists(INVENTORY_RAW_PATH):
        raise DataLoadError(f"Inventory data file not found: {INVENTORY_RAW_PATH}")
    if not os.path.exists(SALES_RAW_PATH):
        raise DataLoadError(f"Sales data file not found: {SALES_RAW_PATH}")

    try:
        raw_inventory = pd.read_csv(INVENTORY_RAW_PATH)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise DataLoadError(f"Could not parse inventory CSV: {exc}") from exc

    try:
        raw_sales = pd.read_csv(SALES_RAW_PATH)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise DataLoadError(f"Could not parse sales CSV: {exc}") from exc

    if raw_inventory.empty:
        raise DataLoadError("Inventory data file is empty.")

    inventory_df, inv_report = clean_inventory_data(raw_inventory)
    sales_df, sales_report = clean_sales_data(
        raw_sales, valid_product_ids=set(inventory_df["product_id"])
    )

    _cache["inventory"] = inventory_df
    _cache["sales"] = sales_df
    _cache["inventory_report"] = inv_report
    _cache["sales_report"] = sales_report
    _cache["loaded"] = True


def get_inventory(force_reload=False) -> pd.DataFrame:
    with _lock:
        if force_reload or not _cache["loaded"]:
            _load_from_disk()
    return _cache["inventory"].copy()


def get_sales(force_reload=False) -> pd.DataFrame:
    with _lock:
        if force_reload or not _cache["loaded"]:
            _load_from_disk()
    return _cache["sales"].copy()


def get_data_quality_report(force_reload=False) -> dict:
    with _lock:
        if force_reload or not _cache["loaded"]:
            _load_from_disk()
    return {
        "inventory": _cache["inventory_report"],
        "sales": _cache["sales_report"],
    }


def reload_data():
    """Force re-read + re-clean of the CSVs from disk. Returns the fresh
    data-quality report."""
    with _lock:
        _load_from_disk()
    return get_data_quality_report()
