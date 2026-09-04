/* insights.js */

function summaryCard(label, value, variant) {
  return `<div class="kpi-card kpi-card--${variant}"><p class="kpi-label">${label}</p><p class="kpi-value">${value}</p></div>`;
}

function daysOfSupplyLabel(v) {
  if (v === null || v === undefined) return "—";
  if (v === Infinity || v > 9998) return "∞";
  return Math.round(v);
}

async function loadInsights() {
  const summaryBox = document.getElementById("insight-summary");
  const restockBody = document.getElementById("restock-tbody");
  const fastBody = document.getElementById("fast-moving-tbody");
  const slowBody = document.getElementById("slow-moving-tbody");
  const overstockBody = document.getElementById("overstocked-tbody");
  const neverSoldBody = document.getElementById("never-sold-tbody");

  try {
    const data = await API.get("/api/insights");
    const s = data.summary;

    summaryBox.innerHTML = [
      summaryCard("Restock needed", formatNumber(s.restock_needed_count), "danger"),
      summaryCard("Fast-moving products", formatNumber(s.fast_moving_count), "ok"),
      summaryCard("Slow-moving products", formatNumber(s.slow_moving_count), "warn"),
      summaryCard("Overstocked", `${formatNumber(s.overstocked_count)}`, "accent"),
    ].join("");

    restockBody.innerHTML = data.restock_recommendations.length
      ? data.restock_recommendations.map((p) => `
          <tr>
            <td>${escapeHtml(p.product_name)}</td>
            <td>${escapeHtml(p.supplier)}</td>
            <td class="mono">${formatNumber(p.stock_quantity)}</td>
            <td class="mono">${p.lead_time_days}</td>
            <td class="mono">${p.avg_daily_sales}</td>
            <td class="mono">${daysOfSupplyLabel(p.projected_stockout_days)}</td>
            <td class="mono">${formatNumber(p.recommended_reorder_qty)}</td>
          </tr>`).join("")
      : `<tr><td colspan="7" class="empty-state">No products currently at risk of stocking out before restock.</td></tr>`;

    fastBody.innerHTML = data.fast_moving.length
      ? data.fast_moving.map((p) => `
          <tr><td>${escapeHtml(p.product_name)}</td><td>${escapeHtml(p.category)}</td>
          <td class="mono">${p.avg_daily_sales}</td><td class="mono">${formatNumber(p.stock_quantity)}</td></tr>`).join("")
      : `<tr><td colspan="4" class="empty-state">Not enough sales data yet.</td></tr>`;

    slowBody.innerHTML = data.slow_moving.length
      ? data.slow_moving.map((p) => `
          <tr><td>${escapeHtml(p.product_name)}</td><td>${escapeHtml(p.category)}</td>
          <td class="mono">${p.avg_daily_sales}</td><td class="mono">${formatNumber(p.stock_quantity)}</td></tr>`).join("")
      : `<tr><td colspan="4" class="empty-state">No slow-moving products identified.</td></tr>`;

    overstockBody.innerHTML = data.overstocked.length
      ? data.overstocked.map((p) => `
          <tr><td>${escapeHtml(p.product_name)}</td><td>${escapeHtml(p.category)}</td>
          <td class="mono">${formatNumber(p.stock_quantity)}</td>
          <td class="mono">${daysOfSupplyLabel(p.days_of_supply)}</td>
          <td class="mono">${formatCurrency(p.inventory_value)}</td></tr>`).join("")
      : `<tr><td colspan="5" class="empty-state">No overstocked products identified.</td></tr>`;

    neverSoldBody.innerHTML = data.never_sold.length
      ? data.never_sold.map((p) => `
          <tr><td>${escapeHtml(p.product_name)}</td><td>${escapeHtml(p.category)}</td>
          <td>${escapeHtml(p.supplier)}</td><td class="mono">${formatNumber(p.stock_quantity)}</td></tr>`).join("")
      : `<tr><td colspan="4" class="empty-state">Every in-stock product has sold at least once.</td></tr>`;

  } catch (err) {
    summaryBox.innerHTML = `<div class="error-state">Could not load insights: ${escapeHtml(err.message)}</div>`;
  }
}

window.onDataReloaded = loadInsights;
document.addEventListener("DOMContentLoaded", loadInsights);
