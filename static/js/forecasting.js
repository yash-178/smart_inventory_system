/* forecasting.js */

async function loadForecastOptions() {
  const productSelect = document.getElementById("product-select");
  const categorySelect = document.getElementById("category-select");
  try {
    const data = await API.get("/api/forecast/options");
    productSelect.innerHTML = data.products
      .map((p) => `<option value="${escapeHtml(p.product_id)}">${escapeHtml(p.product_name)} (${escapeHtml(p.product_id)})</option>`)
      .join("");
    categorySelect.innerHTML = data.categories
      .map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`)
      .join("");
  } catch (err) {
    showToast(`Could not load product list: ${err.message}`, "error");
  }
}

function wireScopeToggle() {
  const scopeSelect = document.getElementById("forecast-scope");
  scopeSelect.addEventListener("change", () => {
    const isProduct = scopeSelect.value === "product";
    document.getElementById("product-group").style.display = isProduct ? "flex" : "none";
    document.getElementById("category-group").style.display = isProduct ? "none" : "flex";
  });
}

function renderForecastChart(result) {
  const el = document.getElementById("forecast-chart");
  const traces = [
    {
      type: "scatter", mode: "lines", name: "Historical daily sales",
      x: result.history_dates, y: result.history_values,
      line: { color: "#8890A0", width: 1.5 },
    },
    {
      type: "scatter", mode: "lines+markers", name: "Forecast",
      x: result.forecast_dates, y: result.forecast_values,
      line: { color: "#E8963A", width: 2.5, dash: "dot" },
      marker: { size: 5 },
    },
  ];
  Plotly.newPlot(el, traces, {
    ...plotlyBaseLayout(),
    yaxis: { ...plotlyBaseLayout().yaxis, title: "Units sold / day" },
    legend: { orientation: "h", y: 1.15 },
    margin: { t: 40, r: 20, l: 55, b: 40 },
  }, PLOTLY_CONFIG);
}

function renderRecommendation(result) {
  const panel = document.getElementById("recommendation-panel");
  let methodNote = `<span class="tag">Method used: ${escapeHtml(result.method_used.replace("_", " "))}</span>`;
  if (result.fallback_used) {
    methodNote += ` <span class="tag" style="border-color:#E8963A;color:#CE7F27;">Fell back from "${escapeHtml(result.requested_method.replace("_", " "))}" — not enough history</span>`;
  }

  let recHtml = "";
  if (result.recommendation) {
    const rec = result.recommendation;
    recHtml = `
      <div class="recommendation-box ${rec.action_needed ? "action-needed" : ""}">
        <p class="panel-title" style="margin-bottom:10px;">Restocking recommendation</p>
        <div class="quality-grid">
          <div class="quality-item">Current stock<div class="val">${formatNumber(rec.current_stock)}</div></div>
          <div class="quality-item">Supplier lead time<div class="val">${rec.lead_time_days} days</div></div>
          <div class="quality-item">Projected demand (lead time)<div class="val">${formatNumber(rec.projected_demand_during_lead_time)}</div></div>
          <div class="quality-item">Recommended reorder qty<div class="val">${formatNumber(rec.recommended_reorder_qty)}</div></div>
        </div>
        <p style="margin:12px 0 0; font-size:12.5px; color:${rec.action_needed ? "#7A4E14" : "#4B5563"};">
          ${rec.action_needed
            ? "Projected demand during the supplier lead time exceeds current stock — place a reorder soon."
            : "Current stock comfortably covers projected demand through the next restock cycle."}
        </p>
      </div>`;
  }

  panel.innerHTML = `
    <div class="panel">
      <div class="panel-header">
        <div>
          <p class="panel-title">Forecast summary</p>
          <p class="panel-desc">Total &amp; average projected demand over the selected horizon</p>
        </div>
      </div>
      <div class="tag-row">${methodNote}</div>
      <div class="quality-grid">
        <div class="quality-item">Total forecast demand<div class="val">${formatNumber(result.total_forecast_demand)}</div></div>
        <div class="quality-item">Avg. daily forecast<div class="val">${formatNumber(result.avg_daily_forecast)}</div></div>
      </div>
      ${recHtml}
    </div>`;
}

async function runForecast() {
  const scope = document.getElementById("forecast-scope").value;
  const method = document.getElementById("method-select").value;
  const periods = Number(document.getElementById("periods-input").value);
  const statusBox = document.getElementById("forecast-status");
  const chartBox = document.getElementById("forecast-chart");
  const recBox = document.getElementById("recommendation-panel");
  const runBtn = document.getElementById("run-forecast-btn");

  if (!Number.isFinite(periods) || periods < 1 || periods > 180) {
    statusBox.innerHTML = `<div class="alert-banner alert-banner--warn">Forecast horizon must be between 1 and 180 days.</div>`;
    return;
  }

  let query;
  if (scope === "product") {
    const pid = document.getElementById("product-select").value;
    if (!pid) { statusBox.innerHTML = `<div class="alert-banner alert-banner--warn">No product selected.</div>`; return; }
    query = `product_id=${encodeURIComponent(pid)}`;
  } else {
    const cat = document.getElementById("category-select").value;
    if (!cat) { statusBox.innerHTML = `<div class="alert-banner alert-banner--warn">No category selected.</div>`; return; }
    query = `category=${encodeURIComponent(cat)}`;
  }

  statusBox.innerHTML = "";
  recBox.innerHTML = "";
  chartBox.innerHTML = `<div class="loading-state">Running forecast…</div>`;
  runBtn.disabled = true;

  try {
    const result = await API.get(`/api/forecast?${query}&method=${method}&periods=${periods}`);
    renderForecastChart(result);
    renderRecommendation(result);
  } catch (err) {
    chartBox.innerHTML = "";
    statusBox.innerHTML = `<div class="alert-banner alert-banner--danger">${escapeHtml(err.message)}</div>`;
  } finally {
    runBtn.disabled = false;
  }
}

function initForecastingPage() {
  loadForecastOptions();
  wireScopeToggle();
  document.getElementById("run-forecast-btn").addEventListener("click", runForecast);
}

window.onDataReloaded = initForecastingPage;
document.addEventListener("DOMContentLoaded", initForecastingPage);
