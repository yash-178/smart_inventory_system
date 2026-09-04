# Smart Inventory Management System

A professional-grade, full-stack inventory management web application built with Python/Flask, featuring real-time dashboards, demand forecasting, automated alerts, and actionable business insights.

## Overview

This application demonstrates a complete pipeline for inventory data management:

- **Data ingestion & cleaning**: Handles real-world messy data (missing values, duplicates, format inconsistencies, invalid numeric entries)
- **Interactive dashboard**: Real-time KPIs, stock status breakdown, monthly trends, and supplier performance visualizations
- **Product management**: Searchable, filterable, sortable inventory table with bulk operations support
- **Analytics & visualizations**: Category distribution, inventory value by category, supplier performance metrics
- **Demand forecasting**: Three forecasting methods (Moving Average, Linear Regression, Random Forest) with automatic fallback and restocking recommendations
- **Alert system**: Real-time low-stock and out-of-stock alerts with impact quantification
- **Business insights**: Fast-moving/slow-moving analysis, overstocking detection, never-sold products, restocking recommendations
- **Report generation**: PDF summary reports and CSV exports

## Stack

- **Backend**: Python 3.12, Flask 3.1
- **Data processing**: Pandas 3.0, NumPy 2.4
- **ML/Forecasting**: scikit-learn 1.8 (Linear Regression, Random Forest)
- **Charting**: Plotly.js 4.0 (vendored locally for offline use)
- **PDF generation**: ReportLab 4.4
- **Frontend**: Vanilla JavaScript, HTML5, CSS3 (no external frameworks)

## Project Structure

```
inventory_system/
├── app.py                    # Flask application & API routes
├── generate_data.py          # Sample data generator (67 products, 11k+ sales records)
├── modules/
│   ├── __init__.py
│   ├── cleaning.py           # Data validation & cleaning pipeline
│   ├── data_manager.py       # Central data loader with caching
│   ├── analytics.py          # Dashboard & analytics aggregations
│   ├── forecasting.py        # 3 demand forecasting methods + recommendations
│   ├── alerts.py             # Low-stock / out-of-stock detection
│   ├── insights.py           # Velocity analysis, overstocking, restocking logic
│   └── reports.py            # PDF & CSV report generation
├── templates/
│   ├── base.html             # Navigation & layout
│   ├── dashboard.html        # Summary KPIs & overview charts
│   ├── inventory.html        # Product table with search/filter/sort
│   ├── analytics.html        # Detailed analytics charts
│   ├── forecasting.html      # Demand forecasting interface
│   ├── alerts.html           # Low-stock & out-of-stock alerts
│   ├── insights.html         # Business insights (fast/slow-moving, overstocking)
│   ├── reports.html          # PDF/CSV report download
│   ├── 404.html & 500.html   # Error pages
├── static/
│   ├── css/style.css         # Design tokens, responsive layout
│   ├── js/
│   │   ├── main.js           # Shared utilities (API wrapper, formatting, Plotly config)
│   │   ├── dashboard.js      # Dashboard page logic
│   │   ├── inventory.js      # Inventory table state management
│   │   ├── analytics.js      # Chart rendering
│   │   ├── forecasting.js    # Forecast configuration & recommendation display
│   │   ├── alerts.js         # Alert table rendering
│   │   ├── insights.js       # Insight tables & summaries
│   │   └── reports.js        # Report download handlers
│   └── vendor/
│       └── plotly.min.js     # Vendored Plotly (no CDN dependencies)
├── data/
│   ├── inventory_raw.csv     # Raw inventory (with intentional messiness)
│   └── sales_raw.csv         # Raw sales transactions (180 days)
├── generated_reports/        # PDF & CSV exports (auto-created)
└── README.md                 # This file
```

## Setup

### Prerequisites

- Python 3.10+
- pip

## Feature Walkthrough

### 1. Dashboard
- **Summary KPIs**: Total products, categories, suppliers, stock levels, inventory value
- **Status breakdown**: Pie chart of In Stock / Low Stock / Out of Stock products
- **Stock by category**: Bar chart showing units on hand per category
- **Monthly sales trend**: Line chart of sales velocity over the past 6 months
- **Top-selling products**: Horizontal bar chart of units sold
- **Data quality report**: Transparent view of cleaning pipeline results (missing values filled, duplicates removed, invalid prices corrected, etc.)

### 2. Inventory Table
- **Search**: By product name, SKU, category, or supplier (real-time, 350ms debounce)
- **Filters**: By category, status (In Stock / Low Stock / Out of Stock), supplier
- **Sort**: Click column headers to sort ascending/descending by any field
- **Pagination**: Configurable page size (10, 20, 50, 100 per page)
- **Status badges**: Visual indicators (green = In Stock, orange = Low Stock, red = Out of Stock)
- **Currency formatting**: All prices displayed as ₹X,XXX.XX

### 3. Analytics
- **Product stock distribution**: Top 10 products by quantity on hand
- **Inventory value by category**: Pie chart showing capital allocation across categories
- **Monthly sales & revenue trend**: Dual-axis chart (units sold vs. revenue generated)
- **Supplier performance table**: Products supplied, lead times, inventory value, revenue generated, stockout rate

### 4. Demand Forecasting
- **Scope selection**: Forecast for a single product or entire category
- **Methods**: 
  - **Moving Average** (7-day window): Simple, stable baseline
  - **Linear Regression** (day-index trend): Captures gradual growth/decline
  - **Random Forest** (lag features + seasonality): Captures complex patterns; auto-fallsback to Linear Regression if insufficient history
- **Horizon**: Configurable 1–180 days ahead
- **Forecast chart**: Historical daily sales (solid line) vs. projected demand (dashed line)
- **Reorder recommendation**: Automatic calculation based on lead time:
  - Current stock + projected demand during lead time → recommended reorder quantity
  - Actionable UI flag: "Place a reorder soon" if at risk

### 5. Alerts
- **Out of stock**: Products with zero units (bold alert banner + table with supplier & lead times)
- **Low stock**: Products at or below reorder level (warning banner + table)
- **Financial impact**: Estimated lost sales value from out-of-stock items

### 6. Insights
- **Restock needed**: 36 products projected to run out before supplier lead time expires
- **Fast-moving products**: 17 products in top sales velocity quartile (demand flagged for prioritization)
- **Slow-moving products**: 15 products with minimal sales but still holding stock (candidates for promotion/clearance)
- **Overstocked products**: 4 products with >90 days of supply at current velocity (capital optimization opportunity)
- **Never sold**: Products in stock with zero sales history
- **Summary KPIs**: Running tallies of each category for quick assessment

### 7. Reports
- **PDF summary**: Multi-section report (dashboard KPIs, alerts, fast/slow-moving, overstocked, restocking recommendations) — ready to print or email
- **CSV export**: Full inventory table with all fields for use in Excel/Google Sheets

## Data Cleaning Pipeline

The `cleaning.py` module processes raw CSVs to address:
- **Missing values**: Fills numeric fields with median/category-median, text fields with "Unknown"
- **Duplicates**: Keeps last occurrence (assumed most recent update)
- **Type coercion**: Converts strings like "Rs.1234.5" to numeric; parses mixed date formats
- **Case standardization**: Title-cases categories and suppliers
- **Validation**: Corrects negative stock (clips to 0), invalid prices (replaces with fallback)
- **Derived fields**: Computes inventory_value (qty × price) and status (In Stock / Low Stock / Out of Stock)

**Transparency**: The data quality report on the Dashboard surfaces all cleaning actions, showing the user exactly what was fixed.

## Forecasting Methods

All three methods operate on daily time series aggregated from sales transactions, with automatic fallback if data is insufficient:

### Moving Average
- Computes 7-day rolling average of recent sales
- Projects that average forward for the requested horizon
- **Best for**: Stable, seasonal categories with low volatility
- **Minimum history**: 10 days

### Linear Regression
- Fits a line to day-index vs. quantity_sold
- Extrapolates trend forward
- **Best for**: Growing or declining categories with clear directional bias
- **Minimum history**: 10 days

### Random Forest
- Trains 200-tree ensemble using lag features (1, 2, 3, 7, 14 days), day-of-week, and day-index
- Captures complex non-linear patterns and weekly seasonality
- **Automatic fallback**: If <15 usable data points after lag feature creation, silently switches to Linear Regression
- **Best for**: High-frequency, multi-modal categories with repeating patterns
- **Minimum history**: 15 days (for lag feature generation)

All methods return:
- Historical daily values (for charting)
- Forecast values (for the specified horizon)
- Summary statistics (total demand, average daily demand)
- Reorder recommendation (for single-product forecasts)

## Alerts & Recommendations

### Restocking Recommendation Algorithm

For each product at risk of stockout before restock arrival:

```
lead_time_days = supplier's typical transit time (e.g., 7 days)
projected_demand_during_lead_time = avg_daily_sales × lead_time_days
current_stock = on-hand quantity
reorder_level = safety stock threshold

recommended_reorder_qty = max(
  0,
  (avg_daily_sales × (lead_time_days + 30)) - current_stock
)
```

This ensures:
1. Enough stock to cover the lead time without stockout
2. An additional 30 days of buffer (configurable in `forecasting.py`)

### Overstocking Detection

A product is flagged as overstocked if:
- **Days of supply** > 90 days (at current sales pace)
- Currently holding stock
- Has positive sales velocity

**Insight**: Capital locked up that could be deployed elsewhere.

## Error Handling & Edge Cases

### Backend

- **Missing/empty data**: API returns 422 with descriptive error message (e.g., "Not enough sales history to forecast")
- **Invalid product/category**: 404 responses with specific entity names
- **Invalid parameters**: 400 responses (e.g., sort_by column not recognized, page_size out of bounds)
- **Forecast with insufficient history**: Graceful fallback (Random Forest → Linear Regression) with `fallback_used=true` flag in response
- **Out-of-stock product forecasting**: Allowed (treats as zero sales, forecast remains available if any historical sales exist)
- **Reload data**: Thread-safe via mutex lock; re-runs cleaning pipeline and updates cache atomically

### Frontend

- **Network errors**: Toast notifications with error messages
- **Missing data**: Empty states with explanatory messages (e.g., "No overstocked products identified")
- **Console errors**: Graceful fallback to placeholder UI (no breaking errors on chart load failures)
- **Pagination overflow**: Auto-corrects to last available page
- **Form validation**: Disables submit button during request, restores on completion

## Performance Notes

- **Data caching**: Inventory and sales DataFrames are cached in memory on first load; manually reloadable via "Reload & re-clean data" button (useful for development/testing)
- **Pagination**: Inventory table paged server-side to avoid loading all 67+ products at once
- **Chart rendering**: Plotly.js renders incrementally; large datasets (180 days × 67 products = 10k+ points) render in <1s
- **Forecasting**: Linear Regression (<100ms), Random Forest (<500ms per product)

## Sample Data

The `generate_data.py` script creates:
- **67 products** across 9 categories (Electronics, Groceries, Furniture, Apparel, Stationery, Toys, Sports, Home & Kitchen)
- **9 suppliers** with varying lead times (2–8 days) and stockout rates
- **180 days** of daily sales transactions (~11,700 records)
- **Intentional messiness**: Missing values, duplicates, type inconsistencies, negative stock entries, currency-prefixed prices (for the cleaning demo)
- **Deliberate overstocking**: 4 products seeded with >110 days of supply to showcase the overstocking insight
- **Realistic seasonality**: Category-level trends and weekly patterns so forecasting has meaningful signal to capture

## Customization

### Change the reorder buffer period
Edit `modules/forecasting.py`, function `generate_forecast()`:
```python
# Currently 30 days
recommended_reorder_qty = max(0, (daily_v * (lead_time + 30)) - current_stock)
# To 45 days:
recommended_reorder_qty = max(0, (daily_v * (lead_time + 45)) - current_stock)
```

### Change the overstocking threshold
Edit `modules/insights.py`, module constant:
```python
OVERSTOCK_DAYS_THRESHOLD = 90  # Change to 120 for more lenient detection
```

### Regenerate sample data
```bash
python3 -c "from generate_data import ensure_data_exists; ensure_data_exists(force=True)"
```

## Testing

The application includes comprehensive error handling:

```bash
# Run the Flask test client against all endpoints
python3 -c "
import app
c = app.app.test_client()
for url in ['/api/dashboard/summary', '/api/forecast?product_id=P1000']:
    r = c.get(url)
    print(url, r.status_code)
"
```

Key edge cases tested:
- Forecasting with zero sales history (returns error with min-history threshold)
- Invalid sort column (returns 400)
- Out-of-stock product forecast (succeeds if any prior sales exist)
- Random Forest with <15 usable data points (auto-fallback to Linear Regression)
- Page pagination overflow (auto-corrects to last page)
- Report generation with empty alert lists (renders "No items" message)

## Limitations & Future Enhancements

### Current Limitations
- **Single-user**: No authentication or multi-user support
- **In-memory caching**: Data lost on server restart (no persistence layer)
- **Synchronous forecasting**: Large batch forecasts block the UI (candidate for async tasks with Celery)
- **Static sample data**: No direct data upload or edit UI (can regenerate via Python script)

### Future Enhancements
1. **Database persistence**: Replace CSV + memory cache with SQLite/PostgreSQL
2. **User authentication**: Multi-user support with role-based access control
3. **Data upload UI**: Import custom inventory CSVs via web interface
4. **Async forecasting**: Background task queue (Celery + Redis) for large batch operations
5. **Alert routing**: Email/SMS notifications for critical stockouts
6. **Integration APIs**: Webhook triggers to external procurement systems
7. **Advanced forecasting**: Prophet for holiday-aware seasonality, hierarchical forecasting for roll-ups
8. **Audit logging**: Track all inventory changes with user attribution and timestamps

## License

This project is for educational and portfolio demonstration purposes.

## Author

Built as a comprehensive internship project showcasing full-stack data engineering, analytics, and web development skills.
