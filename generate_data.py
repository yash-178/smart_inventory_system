"""
generate_data.py
-----------------
Generates realistic (and intentionally messy) sample datasets for the
Smart Inventory Management System:

  data/inventory_raw.csv  -> product master data (with dirty rows so the
                              cleaning pipeline in modules/cleaning.py has
                              real work to do)
  data/sales_raw.csv      -> 180 days of daily sales transactions used for
                              trends, top-sellers, and demand forecasting

Run once with:  python generate_data.py
The Flask app also imports `ensure_data_exists()` and will call this
automatically on first run if the CSV files are missing.
"""

import os
import random
import numpy as np
import pandas as pd

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INVENTORY_RAW_PATH = os.path.join(DATA_DIR, "inventory_raw.csv")
SALES_RAW_PATH = os.path.join(DATA_DIR, "sales_raw.csv")

CATEGORIES = {
    "Electronics": ["Wireless Mouse", "USB-C Cable", "Bluetooth Speaker", "Laptop Stand",
                    "Mechanical Keyboard", "Webcam HD", "Power Bank 10000mAh", "Smart Watch",
                    "Noise Cancelling Headphones", "HDMI Adapter", "External SSD 1TB", "Router Dual Band"],
    "Groceries": ["Basmati Rice 5kg", "Sunflower Oil 1L", "Green Tea Box", "Almonds 500g",
                  "Whole Wheat Flour 5kg", "Organic Honey 250g", "Instant Coffee Jar", "Peanut Butter 400g",
                  "Mixed Spices Pack", "Brown Sugar 1kg"],
    "Furniture": ["Office Chair", "Study Table", "Bookshelf 5-Tier", "Bean Bag",
                  "Bed Side Table", "Wardrobe 3-Door", "Recliner Sofa", "Dining Table Set"],
    "Apparel": ["Cotton T-Shirt", "Denim Jeans", "Formal Shirt", "Running Shoes",
                "Winter Jacket", "Woolen Socks Pack", "Leather Belt", "Sports Cap"],
    "Stationery": ["A4 Paper Ream", "Gel Pen Pack", "Spiral Notebook", "Sticky Notes Set",
                   "Highlighter Set", "Desk Organizer", "Whiteboard Marker Pack", "Stapler Heavy Duty"],
    "Toys": ["Building Blocks Set", "Remote Control Car", "Puzzle 1000pc", "Board Game Classic",
             "Soft Plush Toy", "Kids Tricycle"],
    "Sports": ["Yoga Mat", "Dumbbell Set 10kg", "Cricket Bat", "Football Size 5",
               "Badminton Racket Pair", "Skipping Rope", "Resistance Bands Set"],
    "Home & Kitchen": ["Non-Stick Pan Set", "Electric Kettle", "Vacuum Flask 1L", "Chopping Board Set",
                       "Mixer Grinder", "LED Table Lamp", "Storage Container Set", "Ceramic Dinner Set"],
}

SUPPLIERS = [
    ("Apex Distributors", 3, 0.97),
    ("Northline Traders", 5, 0.93),
    ("Global Supply Co.", 7, 0.89),
    ("Prime Wholesale", 4, 0.95),
    ("Metro Logistics", 6, 0.91),
    ("Sunrise Vendors", 2, 0.98),
    ("Unity Merchants", 8, 0.86),
    ("BlueLeaf Sourcing", 5, 0.92),
]

CATEGORY_PRICE_RANGE = {
    "Electronics": (400, 9000),
    "Groceries": (60, 900),
    "Furniture": (1500, 25000),
    "Apparel": (250, 3500),
    "Stationery": (30, 700),
    "Toys": (150, 2500),
    "Sports": (200, 6000),
    "Home & Kitchen": (300, 5500),
}


def _random_date_str(start_days_ago, end_days_ago, fmt):
    days_ago = random.randint(end_days_ago, start_days_ago)
    d = pd.Timestamp.today().normalize() - pd.Timedelta(days=days_ago)
    return d.strftime(fmt)


def build_inventory():
    rows = []
    pid = 1000
    for category, products in CATEGORIES.items():
        low, high = CATEGORY_PRICE_RANGE[category]
        for name in products:
            supplier = random.choice(SUPPLIERS)
            unit_price = round(np.random.uniform(low, high), 2)
            unit_cost = round(unit_price * np.random.uniform(0.55, 0.8), 2)
            # base "true" stock level per product, later perturbed for messiness
            base_stock = int(np.random.choice(
                [0, 3, 8, 15, 25, 40, 60, 90, 120, 180],
                p=[0.06, 0.08, 0.10, 0.12, 0.14, 0.14, 0.12, 0.10, 0.08, 0.06]
            ))
            reorder_level = max(5, int(base_stock * np.random.uniform(0.15, 0.35)) if base_stock else 10)
            lead_time_days = supplier[1] + random.randint(-1, 2)
            date_added = _random_date_str(720, 400, "%Y-%m-%d")
            last_restocked = _random_date_str(180, 1, "%d/%m/%Y")  # inconsistent format on purpose

            rows.append({
                "product_id": f"P{pid}",
                "product_name": name,
                "category": category,
                "supplier": supplier[0],
                "stock_quantity": base_stock,
                "reorder_level": reorder_level,
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "lead_time_days": lead_time_days,
                "date_added": date_added,
                "last_restocked_date": last_restocked,
            })
            pid += 1

    df = pd.DataFrame(rows)

    # ---- Intentionally inject messiness for the cleaning pipeline ----
    n = len(df)
    idx = df.index.tolist()

    # 1) Missing values scattered across several columns
    for col, frac in [("unit_price", 0.03), ("stock_quantity", 0.02),
                       ("supplier", 0.03), ("category", 0.015),
                       ("reorder_level", 0.02), ("last_restocked_date", 0.04)]:
        miss_idx = random.sample(idx, max(1, int(n * frac)))
        df.loc[miss_idx, col] = np.nan

    # 2) Inconsistent text casing / whitespace
    case_idx = random.sample(idx, int(n * 0.15))
    for i in case_idx:
        choice = random.choice(["upper", "lower", "pad"])
        if choice == "upper":
            df.at[i, "category"] = str(df.at[i, "category"]).upper()
        elif choice == "lower":
            df.at[i, "supplier"] = str(df.at[i, "supplier"]).lower()
        else:
            df.at[i, "product_name"] = "  " + str(df.at[i, "product_name"]) + "  "

    # 3) Duplicate rows (same product_id re-appended, sometimes with slightly stale data)
    dup_rows = df.sample(6, random_state=1).copy()
    df = pd.concat([df, dup_rows], ignore_index=True)

    # 4) A few invalid / negative numeric entries (data entry errors)
    bad_idx = random.sample(idx, 5)
    for i in bad_idx:
        if i < len(df):
            df.at[i, "stock_quantity"] = -abs(int(np.random.uniform(1, 10)))
    price_bad_idx = random.sample(idx, 3)
    for i in price_bad_idx:
        df.at[i, "unit_price"] = 0

    # 5) unit_price stored as text with currency symbol for a handful of rows
    df["unit_price"] = df["unit_price"].astype(object)
    text_price_idx = random.sample(idx, 4)
    for i in text_price_idx:
        val = df.at[i, "unit_price"]
        if pd.notna(val):
            df.at[i, "unit_price"] = f"Rs.{val}"

    return df


def build_sales(inventory_df):
    """Generate 180 days of daily sales for each product with category-level
    seasonality/trend so forecasting has meaningful signal."""
    days = 180
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days, freq="D")

    category_trend = {cat: np.random.uniform(-0.15, 0.35) for cat in CATEGORIES}
    category_base = {cat: np.random.uniform(2, 12) for cat in CATEGORIES}

    records = []
    clean_products = inventory_df.drop_duplicates(subset=["product_id"])
    for _, prod in clean_products.iterrows():
        pid = prod["product_id"]
        cat = prod["category"] if pd.notna(prod["category"]) else random.choice(list(CATEGORIES.keys()))
        cat = str(cat).strip().title()
        if cat not in CATEGORIES:
            cat = random.choice(list(CATEGORIES.keys()))

        base = category_base[cat] * np.random.uniform(0.4, 1.6)
        trend = category_trend[cat] / days
        weekly_amp = np.random.uniform(0.1, 0.4)
        noise_scale = max(0.5, base * 0.35)

        for t, d in enumerate(dates):
            weekday_factor = 1.25 if d.weekday() >= 5 else 1.0  # weekend bump
            seasonal = 1 + weekly_amp * np.sin(2 * np.pi * (t % 30) / 30)
            expected = base * (1 + trend * t) * weekday_factor * seasonal
            qty = max(0, int(np.random.poisson(max(0.1, expected)) + np.random.normal(0, noise_scale * 0.15)))
            if qty <= 0:
                continue
            unit_price = prod["unit_price"]
            try:
                price_val = float(str(unit_price).replace("Rs.", ""))
            except (ValueError, TypeError):
                price_val = 0.0
            records.append({
                "date": d.strftime("%Y-%m-%d"),
                "product_id": pid,
                "quantity_sold": qty,
                "revenue": round(qty * price_val, 2),
            })

    sales_df = pd.DataFrame(records)

    # Inject minor messiness into sales too: a few duplicate rows and missing revenue
    dup = sales_df.sample(10, random_state=2)
    sales_df = pd.concat([sales_df, dup], ignore_index=True)
    miss_idx = sales_df.sample(15, random_state=3).index
    sales_df.loc[miss_idx, "revenue"] = np.nan

    return sales_df


def _apply_deliberate_overstocking(inv_df, sales_df, product_names, target_days_of_supply=110):
    """Boost stock for a handful of named products to a multiple of their
    *actual* recent sales velocity, guaranteeing they show up as genuinely
    overstocked in the Insights page regardless of how the random category
    velocity landed for that product. Operates after sales are generated
    so the velocity figure is real, not guessed."""
    if sales_df.empty:
        return inv_df

    recent_cutoff = pd.to_datetime(sales_df["date"]).max() - pd.Timedelta(days=30)
    recent = sales_df[pd.to_datetime(sales_df["date"]) >= recent_cutoff]
    velocity = recent.groupby("product_id")["quantity_sold"].sum() / 30.0

    for name in product_names:
        matches = inv_df.index[inv_df["product_name"].str.strip() == name]
        if len(matches) == 0:
            continue
        pid = inv_df.loc[matches[0], "product_id"]
        daily_v = float(velocity.get(pid, 0))
        if daily_v <= 0:
            daily_v = 1.0  # still give it a healthy stock pile even if unsold recently
        new_stock = int(round(daily_v * target_days_of_supply))
        inv_df.loc[inv_df["product_name"].str.strip() == name, "stock_quantity"] = max(new_stock, 200)

    return inv_df


def ensure_data_exists(force=False):
    """Create the raw CSV files if they don't already exist (or force regeneration)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if force or not (os.path.exists(INVENTORY_RAW_PATH) and os.path.exists(SALES_RAW_PATH)):
        inv_df = build_inventory()
        sales_df = build_sales(inv_df)

        inv_df = _apply_deliberate_overstocking(
            inv_df, sales_df,
            product_names=["Skipping Rope", "Sunflower Oil 1L", "Building Blocks Set", "A4 Paper Ream"],
        )

        inv_df.to_csv(INVENTORY_RAW_PATH, index=False)
        sales_df.to_csv(SALES_RAW_PATH, index=False)
        print(f"Generated {len(inv_df)} inventory rows -> {INVENTORY_RAW_PATH}")
        print(f"Generated {len(sales_df)} sales rows -> {SALES_RAW_PATH}")
    else:
        print("Sample data already exists. Use force=True to regenerate.")


if __name__ == "__main__":
    ensure_data_exists(force=True)
