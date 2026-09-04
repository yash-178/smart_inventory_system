"""
app.py
------
Smart Inventory Management System - Flask application entry point.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import os
import traceback

from flask import Flask, render_template, request, jsonify, send_file

from modules import data_manager
from modules import analytics
from modules import alerts as alerts_mod
from modules import insights as insights_mod
from modules import forecasting
from modules import reports

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def error_response(message, status=400):
    return jsonify({"success": False, "error": message}), status


def success_response(data):
    return jsonify({"success": True, "data": data})


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return error_response("Endpoint not found.", 404)
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    traceback.print_exc()
    if request.path.startswith("/api/"):
        return error_response("Internal server error. Please check server logs.", 500)
    return render_template("500.html"), 500


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard_page():
    return render_template("dashboard.html", active="dashboard")


@app.route("/inventory")
def inventory_page():
    return render_template("inventory.html", active="inventory")


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html", active="analytics")


@app.route("/forecasting")
def forecasting_page():
    return render_template("forecasting.html", active="forecasting")


@app.route("/alerts")
def alerts_page():
    return render_template("alerts.html", active="alerts")


@app.route("/insights")
def insights_page():
    return render_template("insights.html", active="insights")


@app.route("/reports")
def reports_page():
    return render_template("reports.html", active="reports")


# ---------------------------------------------------------------------------
# API: Dashboard
# ---------------------------------------------------------------------------

@app.route("/api/dashboard/summary")
def api_dashboard_summary():
    try:
        inventory = data_manager.get_inventory()
        return success_response(analytics.dashboard_summary(inventory))
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/dashboard/charts")
def api_dashboard_charts():
    try:
        inventory = data_manager.get_inventory()
        sales = data_manager.get_sales()
        return success_response({
            "category_distribution": analytics.category_stock_distribution(inventory),
            "status_breakdown": analytics.status_breakdown(inventory),
            "monthly_trend": analytics.monthly_sales_trend(sales),
            "top_selling": analytics.top_selling_products(inventory, sales, n=8),
        })
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/data/quality-report")
def api_data_quality_report():
    try:
        return success_response(data_manager.get_data_quality_report())
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/data/reload", methods=["POST"])
def api_data_reload():
    try:
        report = data_manager.reload_data()
        return success_response(report)
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


# ---------------------------------------------------------------------------
# API: Inventory (search / filter / sort / paginate)
# ---------------------------------------------------------------------------

VALID_SORT_COLUMNS = {
    "product_name", "category", "supplier", "stock_quantity",
    "reorder_level", "unit_price", "inventory_value", "status",
}


@app.route("/api/inventory")
def api_inventory_list():
    try:
        inventory = data_manager.get_inventory()

        search = request.args.get("search", "").strip().lower()
        category = request.args.get("category", "").strip()
        status = request.args.get("status", "").strip()
        supplier = request.args.get("supplier", "").strip()
        sort_by = request.args.get("sort_by", "product_name").strip()
        order = request.args.get("order", "asc").strip().lower()
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)

        if sort_by not in VALID_SORT_COLUMNS:
            return error_response(f"Invalid sort_by column: {sort_by}")
        if order not in {"asc", "desc"}:
            return error_response("order must be 'asc' or 'desc'")
        if page < 1 or page_size < 1 or page_size > 500:
            return error_response("Invalid page or page_size.")

        df = inventory.copy()
        if search:
            mask = (
                df["product_name"].str.lower().str.contains(search, na=False)
                | df["product_id"].str.lower().str.contains(search, na=False)
                | df["category"].str.lower().str.contains(search, na=False)
                | df["supplier"].str.lower().str.contains(search, na=False)
            )
            df = df[mask]
        if category and category.lower() != "all":
            df = df[df["category"] == category]
        if status and status.lower() != "all":
            df = df[df["status"] == status]
        if supplier and supplier.lower() != "all":
            df = df[df["supplier"] == supplier]

        df = df.sort_values(sort_by, ascending=(order == "asc"), na_position="last")

        total_items = int(len(df))
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        page = min(page, total_pages)
        start = (page - 1) * page_size
        page_df = df.iloc[start:start + page_size]

        cols = ["product_id", "product_name", "category", "supplier",
                "stock_quantity", "reorder_level", "unit_price", "unit_cost",
                "inventory_value", "status", "lead_time_days"]
        cols = [c for c in cols if c in page_df.columns]

        return success_response({
            "items": page_df[cols].to_dict(orient="records"),
            "total_items": total_items,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
        })
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/inventory/filters")
def api_inventory_filters():
    try:
        inventory = data_manager.get_inventory()
        return success_response({
            "categories": sorted(inventory["category"].dropna().unique().tolist()),
            "statuses": sorted(inventory["status"].dropna().unique().tolist()),
            "suppliers": sorted(inventory["supplier"].dropna().unique().tolist()),
        })
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


# ---------------------------------------------------------------------------
# API: Analytics
# ---------------------------------------------------------------------------

@app.route("/api/analytics/category-distribution")
def api_analytics_category_distribution():
    try:
        inventory = data_manager.get_inventory()
        return success_response(analytics.category_stock_distribution(inventory))
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/analytics/top-products-by-stock")
def api_analytics_top_products_stock():
    try:
        inventory = data_manager.get_inventory()
        n = request.args.get("n", 10, type=int)
        return success_response(analytics.top_products_by_stock(inventory, n=n))
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/analytics/monthly-trend")
def api_analytics_monthly_trend():
    try:
        sales = data_manager.get_sales()
        return success_response(analytics.monthly_sales_trend(sales))
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/analytics/inventory-value")
def api_analytics_inventory_value():
    try:
        inventory = data_manager.get_inventory()
        return success_response(analytics.inventory_value_by_category(inventory))
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/analytics/supplier-performance")
def api_analytics_supplier_performance():
    try:
        inventory = data_manager.get_inventory()
        sales = data_manager.get_sales()
        return success_response(analytics.supplier_performance(inventory, sales))
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/analytics/top-selling")
def api_analytics_top_selling():
    try:
        inventory = data_manager.get_inventory()
        sales = data_manager.get_sales()
        n = request.args.get("n", 10, type=int)
        return success_response(analytics.top_selling_products(inventory, sales, n=n))
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


# ---------------------------------------------------------------------------
# API: Forecasting
# ---------------------------------------------------------------------------

@app.route("/api/forecast")
def api_forecast():
    try:
        product_id = request.args.get("product_id", "").strip() or None
        category = request.args.get("category", "").strip() or None
        method = request.args.get("method", "linear_regression").strip()
        periods = request.args.get("periods", 30, type=int)

        if not product_id and not category:
            return error_response("Provide either product_id or category.")

        inventory = data_manager.get_inventory()
        sales = data_manager.get_sales()

        if product_id and product_id not in set(inventory["product_id"]):
            return error_response(f"Unknown product_id: {product_id}", 404)
        if category and category not in set(inventory["category"]):
            return error_response(f"Unknown category: {category}", 404)

        result = forecasting.generate_forecast(
            sales, inventory, product_id=product_id, category=category,
            method=method, periods=periods,
        )
        return success_response(result)
    except forecasting.ForecastError as e:
        return error_response(str(e), 422)
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


@app.route("/api/forecast/options")
def api_forecast_options():
    try:
        inventory = data_manager.get_inventory()
        products = inventory[["product_id", "product_name", "category"]].sort_values("product_name")
        return success_response({
            "products": products.to_dict(orient="records"),
            "categories": sorted(inventory["category"].dropna().unique().tolist()),
        })
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


# ---------------------------------------------------------------------------
# API: Alerts
# ---------------------------------------------------------------------------

@app.route("/api/alerts")
def api_alerts():
    try:
        inventory = data_manager.get_inventory()
        return success_response(alerts_mod.get_alerts(inventory))
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


# ---------------------------------------------------------------------------
# API: Insights
# ---------------------------------------------------------------------------

@app.route("/api/insights")
def api_insights():
    try:
        inventory = data_manager.get_inventory()
        sales = data_manager.get_sales()
        return success_response(insights_mod.generate_insights(inventory, sales))
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)


# ---------------------------------------------------------------------------
# API: Reports
# ---------------------------------------------------------------------------

@app.route("/api/reports/generate")
def api_reports_generate():
    try:
        fmt = request.args.get("format", "pdf").strip().lower()
        inventory = data_manager.get_inventory()
        sales = data_manager.get_sales()

        if fmt == "csv":
            path = reports.export_inventory_csv(inventory)
            return send_file(path, as_attachment=True, download_name=os.path.basename(path))
        elif fmt == "pdf":
            path = reports.generate_pdf_report(inventory, sales)
            return send_file(path, as_attachment=True, download_name=os.path.basename(path))
        else:
            return error_response("format must be 'csv' or 'pdf'.")
    except data_manager.DataLoadError as e:
        return error_response(str(e), 500)
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Report generation failed: {e}", 500)


if __name__ == "__main__":
    # Warm the data cache (and generate sample data) before first request.
    try:
        data_manager.get_inventory()
    except data_manager.DataLoadError as e:
        print(f"WARNING: failed to preload data on startup: {e}")
    app.run(debug=True, host="0.0.0.0", port=5000)
