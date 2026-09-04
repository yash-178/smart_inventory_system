/* dashboard.js */

function kpiCard(label, value, sub, variant) {
  return `
    <div class="kpi-card kpi-card--${variant}">
      <p class="kpi-label">${label}</p>
      <p class="kpi-value">${value}</p>
      ${sub ? `<p class="kpi-sub">${sub}</p>` : ""}
    </div>`;
}

async function loadKpis() {
  const grid = document.getElementById("kpi-grid");
  try {
    const s = await API.get("/api/dashboard/summary");
    grid.innerHTML = [
      kpiCard("Total products", formatNumber(s.total_products), `${s.total_categories} categories · ${s.total_suppliers} suppliers`, "accent"),
      kpiCard("Available stock", formatNumber(s.total_stock_units), `${formatNumber(s.in_stock_count)} products in stock`, "ok"),
      kpiCard("Low stock", formatNumber(s.low_stock_count), "At or below reorder level", "warn"),
      kpiCard("Out of stock", formatNumber(s.out_of_stock_count), "Needs immediate restock", "danger"),
      kpiCard("Inventory value", formatCurrency(s.total_inventory_value), `Avg unit price ${formatCurrency(s.avg_unit_price)}`, "accent"),
    ].join("");
  } catch (err) {
    grid.innerHTML = `<div class="error-state">Could not load dashboard summary: ${escapeHtml(err.message)}</div>`;
  }
}

async function loadCharts() {
  try {
    const charts = await API.get("/api/dashboard/charts");
    renderCategoryChart(charts.category_distribution);
    renderStatusChart(charts.status_breakdown);
    renderMonthlyChart(charts.monthly_trend);
    renderTopSellingChart(charts.top_selling);
  } catch (err) {
    showToast(`Could not load charts: ${err.message}`, "error");
    ["chart-category", "chart-status", "chart-monthly", "chart-topselling"].forEach((id) => {
      document.getElementById(id).innerHTML = `<div class="error-state">Chart unavailable.</div>`;
    });
  }
}

function renderCategoryChart(data) {
  const el = document.getElementById("chart-category");
  if (!data.categories.length) {
    el.innerHTML = `<div class="empty-state">No category data available.</div>`;
    return;
  }
  Plotly.newPlot(el, [{
    type: "bar",
    x: data.categories,
    y: data.total_stock,
    marker: { color: "#1E3350" },
    hovertemplate: "%{x}<br>%{y} units<extra></extra>",
  }], { ...plotlyBaseLayout(), yaxis: { ...plotlyBaseLayout().yaxis, title: "Units in stock" } }, PLOTLY_CONFIG);
}

function renderStatusChart(data) {
  const el = document.getElementById("chart-status");
  if (!data.values.some((v) => v > 0)) {
    el.innerHTML = `<div class="empty-state">No status data available.</div>`;
    return;
  }
  Plotly.newPlot(el, [{
    type: "pie",
    labels: data.labels,
    values: data.values,
    hole: 0.55,
    marker: { colors: ["#2E9E6D", "#E8963A", "#D6455A"] },
    textinfo: "label+percent",
  }], { ...plotlyBaseLayout(), showlegend: false }, PLOTLY_CONFIG);
}

function renderMonthlyChart(data) {
  const el = document.getElementById("chart-monthly");
  if (!data.months.length) {
    el.innerHTML = `<div class="empty-state">No sales history available yet.</div>`;
    return;
  }
  Plotly.newPlot(el, [{
    type: "scatter",
    mode: "lines+markers",
    x: data.months,
    y: data.units_sold,
    line: { color: "#E8963A", width: 3 },
    marker: { size: 6 },
    fill: "tozeroy",
    fillcolor: "rgba(232,150,58,0.10)",
    hovertemplate: "%{x}<br>%{y} units sold<extra></extra>",
  }], { ...plotlyBaseLayout(), yaxis: { ...plotlyBaseLayout().yaxis, title: "Units sold" } }, PLOTLY_CONFIG);
}

function renderTopSellingChart(data) {
  const el = document.getElementById("chart-topselling");
  if (!data.product_names.length) {
    el.innerHTML = `<div class="empty-state">No sales recorded yet.</div>`;
    return;
  }
  const names = [...data.product_names].reverse();
  const units = [...data.units_sold].reverse();
  Plotly.newPlot(el, [{
    type: "bar",
    orientation: "h",
    x: units,
    y: names,
    marker: { color: "#2E9E6D" },
    hovertemplate: "%{y}<br>%{x} units<extra></extra>",
  }], { ...plotlyBaseLayout(), margin: { t: 20, r: 20, l: 160, b: 40 } }, PLOTLY_CONFIG);
}

function qualityItem(label, value) {
  return `<div class="quality-item"><div>${label}</div><div class="val">${value}</div></div>`;
}

async function loadQualityReport() {
  const box = document.getElementById("quality-report");
  try {
    const report = await API.get("/api/data/quality-report");
    const inv = report.inventory;
    const sales = report.sales;
    box.innerHTML = `
      <p class="panel-desc" style="margin-bottom:10px;">Inventory source (${inv.rows_before} → ${inv.rows_after} rows)</p>
      <div class="quality-grid" style="margin-bottom:16px;">
        ${qualityItem("Missing values filled", inv.missing_values_filled)}
        ${qualityItem("Duplicate rows removed", inv.duplicate_rows_removed)}
        ${qualityItem("Rows dropped (no ID)", inv.rows_dropped_missing_id)}
        ${qualityItem("Negative stock corrected", inv.negative_stock_corrected)}
        ${qualityItem("Invalid prices corrected", inv.invalid_price_corrected)}
      </div>
      <p class="panel-desc" style="margin-bottom:10px;">Sales source (${sales.rows_before} → ${sales.rows_after} rows)</p>
      <div class="quality-grid">
        ${qualityItem("Duplicate rows removed", sales.duplicate_rows_removed)}
        ${qualityItem("Rows dropped (bad key fields)", sales.rows_dropped_missing_key_fields)}
        ${qualityItem("Missing revenue filled", sales.missing_revenue_filled)}
        ${qualityItem("Rows dropped (unknown product)", sales.rows_dropped_unknown_product)}
      </div>`;
  } catch (err) {
    box.innerHTML = `<div class="error-state">Could not load data quality report: ${escapeHtml(err.message)}</div>`;
  }
}

function loadDashboard() {
  loadKpis();
  loadCharts();
  loadQualityReport();
}

window.onDataReloaded = loadDashboard;
document.addEventListener("DOMContentLoaded", loadDashboard);
