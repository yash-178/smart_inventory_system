/* alerts.js */

async function loadAlerts() {
  const summaryBox = document.getElementById("alert-summary");
  const oosBody = document.getElementById("oos-tbody");
  const lowBody = document.getElementById("low-stock-tbody");

  try {
    const data = await API.get("/api/alerts");

    let banners = "";
    if (data.out_of_stock_count > 0) {
      banners += `<div class="alert-banner alert-banner--danger">
        <strong>${data.out_of_stock_count}</strong>&nbsp;product(s) are completely out of stock — an estimated
        ${formatCurrency(data.potential_lost_value)} in potential sales value is at risk.
      </div>`;
    }
    if (data.low_stock_count > 0) {
      banners += `<div class="alert-banner alert-banner--warn">
        <strong>${data.low_stock_count}</strong>&nbsp;product(s) are at or below their reorder level and should be restocked soon.
      </div>`;
    }
    if (!banners) {
      banners = `<div class="alert-banner" style="background:#E1F4EC;color:#1D6B4C;border:1px solid #BFE6D4;">All products are adequately stocked. No alerts right now.</div>`;
    }
    summaryBox.innerHTML = banners;

    oosBody.innerHTML = data.out_of_stock_items.length
      ? data.out_of_stock_items.map((p) => `
          <tr>
            <td class="mono">${escapeHtml(p.product_id)}</td>
            <td>${escapeHtml(p.product_name)}</td>
            <td>${escapeHtml(p.category)}</td>
            <td>${escapeHtml(p.supplier)}</td>
            <td class="mono">${formatNumber(p.reorder_level)}</td>
            <td class="mono">${p.lead_time_days ?? "—"}</td>
          </tr>`).join("")
      : `<tr><td colspan="6" class="empty-state">No out-of-stock products. Nice work.</td></tr>`;

    lowBody.innerHTML = data.low_stock_items.length
      ? data.low_stock_items.map((p) => `
          <tr>
            <td class="mono">${escapeHtml(p.product_id)}</td>
            <td>${escapeHtml(p.product_name)}</td>
            <td>${escapeHtml(p.category)}</td>
            <td>${escapeHtml(p.supplier)}</td>
            <td class="mono">${formatNumber(p.stock_quantity)}</td>
            <td class="mono">${formatNumber(p.reorder_level)}</td>
            <td class="mono">${formatCurrency(p.inventory_value)}</td>
          </tr>`).join("")
      : `<tr><td colspan="7" class="empty-state">No low-stock products right now.</td></tr>`;
  } catch (err) {
    summaryBox.innerHTML = `<div class="alert-banner alert-banner--danger">Could not load alerts: ${escapeHtml(err.message)}</div>`;
    oosBody.innerHTML = `<tr><td colspan="6" class="error-state">Unavailable</td></tr>`;
    lowBody.innerHTML = `<tr><td colspan="7" class="error-state">Unavailable</td></tr>`;
  }
}

window.onDataReloaded = loadAlerts;
document.addEventListener("DOMContentLoaded", loadAlerts);
