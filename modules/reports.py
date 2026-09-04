"""
reports.py
-----------
Generates downloadable inventory reports:
  - CSV export of the full cleaned inventory (or a filtered subset)
  - A multi-section PDF summary report (dashboard KPIs, alerts, insights)
    built with ReportLab.

Files are written to the `generated_reports/` directory and returned as a
path for Flask's send_file().
"""

import os
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)

from modules import analytics, alerts as alerts_mod, insights as insights_mod

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generated_reports")


def _ensure_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def export_inventory_csv(inventory: pd.DataFrame) -> str:
    _ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORTS_DIR, f"inventory_export_{timestamp}.csv")
    export_cols = ["product_id", "product_name", "category", "supplier",
                   "stock_quantity", "reorder_level", "unit_price", "unit_cost",
                   "inventory_value", "status", "lead_time_days"]
    export_cols = [c for c in export_cols if c in inventory.columns]
    inventory[export_cols].to_csv(path, index=False)
    return path


def _fmt_currency(value):
    """ReportLab's built-in Helvetica font can't render the ₹ glyph, so use
    a plain-text 'Rs.' prefix in the PDF instead of the ₹ symbol used in the
    web UI."""
    return f"Rs. {value:,.2f}"


def _kpi_table(summary: dict):
    data = [
        ["Metric", "Value"],
        ["Total Products", summary["total_products"]],
        ["Categories", summary["total_categories"]],
        ["Suppliers", summary["total_suppliers"]],
        ["Total Stock Units", summary["total_stock_units"]],
        ["In Stock", summary["in_stock_count"]],
        ["Low Stock", summary["low_stock_count"]],
        ["Out of Stock", summary["out_of_stock_count"]],
        ["Total Inventory Value", _fmt_currency(summary["total_inventory_value"])],
        ["Average Unit Price", _fmt_currency(summary["avg_unit_price"])],
    ]
    table = Table(data, colWidths=[8 * cm, 6 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2a44")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5dd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _list_table(records, columns, headers, col_widths):
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle("TableHeader", parent=styles["Normal"], fontName="Helvetica-Bold",
                                   fontSize=8, textColor=colors.white, leading=10)
    header_row = [Paragraph(h, header_style) for h in headers]
    data = [header_row]
    for r in records:
        row = []
        for c in columns:
            val = r.get(c, "")
            if isinstance(val, float):
                val = round(val, 2)
            row.append(str(val) if val is not None else "-")
        data.append(row)
    if len(data) == 1:
        data.append(["No items found"] + [""] * (len(headers) - 1))
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3a5a97")),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d5dd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def generate_pdf_report(inventory: pd.DataFrame, sales: pd.DataFrame) -> str:
    _ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORTS_DIR, f"inventory_report_{timestamp}.pdf")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=20,
                                  textColor=colors.HexColor("#1f2a44"))
    heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], spaceBefore=14,
                                    textColor=colors.HexColor("#1f2a44"))
    normal_style = styles["Normal"]

    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    story = []

    story.append(Paragraph("Smart Inventory Management System", title_style))
    story.append(Paragraph(f"Inventory Report — Generated {datetime.now().strftime('%d %b %Y, %I:%M %p')}", normal_style))
    story.append(Spacer(1, 0.5 * cm))

    summary = analytics.dashboard_summary(inventory)
    story.append(Paragraph("1. Dashboard Summary", heading_style))
    story.append(_kpi_table(summary))

    alert_data = alerts_mod.get_alerts(inventory)
    story.append(Paragraph("2. Low Stock Alerts", heading_style))
    story.append(_list_table(
        alert_data["low_stock_items"][:15],
        ["product_name", "category", "stock_quantity", "reorder_level", "supplier"],
        ["Product", "Category", "Stock", "Reorder Lvl", "Supplier"],
        [5.5 * cm, 3 * cm, 2 * cm, 2.5 * cm, 3.5 * cm],
    ))

    story.append(Paragraph("3. Out of Stock Alerts", heading_style))
    story.append(_list_table(
        alert_data["out_of_stock_items"][:15],
        ["product_name", "category", "reorder_level", "supplier", "lead_time_days"],
        ["Product", "Category", "Reorder Lvl", "Supplier", "Lead (days)"],
        [5 * cm, 3 * cm, 2.5 * cm, 3.5 * cm, 3 * cm],
    ))

    story.append(PageBreak())
    insight_data = insights_mod.generate_insights(inventory, sales)

    story.append(Paragraph("4. Fast-Moving Products", heading_style))
    story.append(_list_table(
        insight_data["fast_moving"][:10],
        ["product_name", "category", "avg_daily_sales", "stock_quantity"],
        ["Product", "Category", "Avg Daily Sales", "Current Stock"],
        [6 * cm, 4 * cm, 3.5 * cm, 3 * cm],
    ))

    story.append(Paragraph("5. Slow-Moving Products", heading_style))
    story.append(_list_table(
        insight_data["slow_moving"][:10],
        ["product_name", "category", "avg_daily_sales", "stock_quantity"],
        ["Product", "Category", "Avg Daily Sales", "Current Stock"],
        [6 * cm, 4 * cm, 3.5 * cm, 3 * cm],
    ))

    story.append(Paragraph("6. Overstocked Products", heading_style))
    story.append(_list_table(
        insight_data["overstocked"][:10],
        ["product_name", "category", "stock_quantity", "days_of_supply"],
        ["Product", "Category", "Stock", "Days of Supply"],
        [6 * cm, 4 * cm, 3 * cm, 3.5 * cm],
    ))

    story.append(Paragraph("7. Restocking Recommendations", heading_style))
    story.append(_list_table(
        insight_data["restock_recommendations"][:15],
        ["product_name", "supplier", "stock_quantity", "lead_time_days", "recommended_reorder_qty"],
        ["Product", "Supplier", "Stock", "Lead (days)", "Reorder Qty"],
        [5 * cm, 4 * cm, 2.5 * cm, 3 * cm, 3 * cm],
    ))

    doc.build(story)
    return path
