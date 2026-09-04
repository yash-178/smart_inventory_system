/* analytics.js */

async function loadTopStockChart() {
  const el = document.getElementById("chart-top-stock");
  try {
    const data = await API.get("/api/analytics/top-products-by-stock?n=10");
    if (!data.product_names.length) {
      el.innerHTML = `<div class="empty-state">No products to display.</div>`;
      return;
    }
    const names = [...data.product_names].reverse();
    const stock = [...data.stock_quantity].reverse();
    Plotly.newPlot(el, [{
      type: "bar", orientation: "h", x: stock, y: names,
      marker: { color: "#1E3350" },
      hovertemplate: "%{y}<br>%{x} units<extra></extra>",
    }], { ...plotlyBaseLayout(), margin: { t: 20, r: 20, l: 170, b: 40 } }, PLOTLY_CONFIG);
  } catch (err) {
    el.innerHTML = `<div class="error-state">${escapeHtml(err.message)}</div>`;
  }
}

async function loadInventoryValueChart() {
  const el = document.getElementById("chart-inv-value");
  try {
    const data = await API.get("/api/analytics/inventory-value");
    if (!data.categories.length) {
      el.innerHTML = `<div class="empty-state">No inventory value data.</div>`;
      return;
    }
    Plotly.newPlot(el, [{
      type: "pie", labels: data.categories, values: data.inventory_value, hole: 0.5,
      textinfo: "label+percent",
    }], { ...plotlyBaseLayout(), showlegend: false }, PLOTLY_CONFIG);
  } catch (err) {
    el.innerHTML = `<div class="error-state">${escapeHtml(err.message)}</div>`;
  }
}

async function loadMonthlyRevenueChart() {
  const el = document.getElementById("chart-monthly-revenue");
  try {
    const data = await API.get("/api/analytics/monthly-trend");
    if (!data.months.length) {
      el.innerHTML = `<div class="empty-state">No sales history available.</div>`;
      return;
    }
    Plotly.newPlot(el, [
      { type: "bar", name: "Units sold", x: data.months, y: data.units_sold, yaxis: "y", marker: { color: "#1E3350" } },
      { type: "scatter", mode: "lines+markers", name: "Revenue (₹)", x: data.months, y: data.revenue, yaxis: "y2", line: { color: "#E8963A", width: 3 } },
    ], {
      ...plotlyBaseLayout(),
      yaxis: { ...plotlyBaseLayout().yaxis, title: "Units sold" },
      yaxis2: { title: "Revenue (₹)", overlaying: "y", side: "right", gridcolor: "transparent" },
      legend: { orientation: "h", y: 1.15 },
      margin: { t: 40, r: 60, l: 55, b: 40 },
    }, PLOTLY_CONFIG);
  } catch (err) {
    el.innerHTML = `<div class="error-state">${escapeHtml(err.message)}</div>`;
  }
}

async function loadSupplierPerformance() {
  const tbody = document.getElementById("supplier-tbody");
  try {
    const data = await API.get("/api/analytics/supplier-performance");
    if (!data.suppliers.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No supplier data available.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.suppliers.map((sup, i) => `
      <tr>
        <td>${escapeHtml(sup)}</td>
        <td class="mono">${formatNumber(data.product_count[i])}</td>
        <td class="mono">${data.avg_lead_time_days[i]}</td>
        <td class="mono">${formatCurrency(data.total_inventory_value[i])}</td>
        <td class="mono">${formatCurrency(data.total_revenue[i])}</td>
        <td class="mono">${(data.stockout_rate[i] * 100).toFixed(1)}%</td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="error-state">${escapeHtml(err.message)}</td></tr>`;
  }
}

async function loadTopSellingChart() {
  const el = document.getElementById("chart-top-selling");
  try {
    const data = await API.get("/api/analytics/top-selling?n=10");
    if (!data.product_names.length) {
      el.innerHTML = `<div class="empty-state">No sales recorded yet.</div>`;
      return;
    }
    Plotly.newPlot(el, [
      { type: "bar", name: "Units sold", x: data.product_names, y: data.units_sold, marker: { color: "#2E9E6D" } },
    ], {
      ...plotlyBaseLayout(),
      xaxis: { ...plotlyBaseLayout().xaxis, tickangle: -30 },
      yaxis: { ...plotlyBaseLayout().yaxis, title: "Units sold" },
      margin: { t: 20, r: 20, l: 50, b: 110 },
    }, PLOTLY_CONFIG);
  } catch (err) {
    el.innerHTML = `<div class="error-state">${escapeHtml(err.message)}</div>`;
  }
}

function loadAnalyticsPage() {
  loadTopStockChart();
  loadInventoryValueChart();
  loadMonthlyRevenueChart();
  loadSupplierPerformance();
  loadTopSellingChart();
}

window.onDataReloaded = loadAnalyticsPage;
document.addEventListener("DOMContentLoaded", loadAnalyticsPage);
