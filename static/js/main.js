/* ==========================================================================
   main.js — shared utilities used across every page
   ========================================================================== */

const API = {
  async get(url) {
    let res;
    try {
      res = await fetch(url);
    } catch (networkErr) {
      throw new Error("Network error: could not reach the server.");
    }
    let payload;
    try {
      payload = await res.json();
    } catch (parseErr) {
      throw new Error("Received an invalid response from the server.");
    }
    if (!res.ok || payload.success === false) {
      throw new Error(payload.error || `Request failed (${res.status})`);
    }
    return payload.data;
  },

  async post(url) {
    let res;
    try {
      res = await fetch(url, { method: "POST" });
    } catch (networkErr) {
      throw new Error("Network error: could not reach the server.");
    }
    let payload;
    try {
      payload = await res.json();
    } catch (parseErr) {
      throw new Error("Received an invalid response from the server.");
    }
    if (!res.ok || payload.success === false) {
      throw new Error(payload.error || `Request failed (${res.status})`);
    }
    return payload.data;
  },
};

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type === "error" ? "toast--error" : type === "success" ? "toast--success" : ""}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4200);
}

function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return "₹" + Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toLocaleString("en-IN");
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function statusBadgeClass(status) {
  if (status === "In Stock") return "badge--ok";
  if (status === "Low Stock") return "badge--warn";
  if (status === "Out of Stock") return "badge--danger";
  return "";
}

function debounce(fn, delay = 300) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/* ---- Global chrome: data status pill + reload button ------------------- */

async function refreshDataStatusPill() {
  const pill = document.getElementById("data-status");
  if (!pill) return;
  try {
    const summary = await API.get("/api/dashboard/summary");
    pill.textContent = `${summary.total_products} products loaded`;
    pill.className = "status-pill status-pill--ok";
  } catch (err) {
    pill.textContent = "Data error";
    pill.className = "status-pill status-pill--error";
  }
}

function wireReloadButton() {
  const btn = document.getElementById("reload-data-btn");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = "Cleaning data…";
    try {
      await API.post("/api/data/reload");
      showToast("Data reloaded and re-cleaned successfully.", "success");
      await refreshDataStatusPill();
      if (typeof window.onDataReloaded === "function") {
        window.onDataReloaded();
      }
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  refreshDataStatusPill();
  wireReloadButton();
});

/* Common Plotly layout tokens so every chart shares the same visual voice.
   IMPORTANT: this must be a factory function, not a shared object literal.
   Plotly.newPlot mutates the layout object (and its axis sub-objects) that
   you pass to it in place — writing computed `type`/`range`/`autorange`
   properties directly onto them. If multiple charts on the same page ever
   shared the same nested xaxis/yaxis object by reference, each chart's
   render would corrupt the axis config for every chart drawn after it. */
const PLOTLY_COLORWAY = ["#1E3350", "#E8963A", "#2E9E6D", "#8890A0", "#D6455A", "#4B5563"];

function plotlyBaseLayout() {
  return {
    font: { family: "IBM Plex Sans, sans-serif", size: 12, color: "#1C2431" },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    colorway: PLOTLY_COLORWAY,
    margin: { t: 30, r: 20, l: 50, b: 40 },
    xaxis: { gridcolor: "#EEF0F3", zeroline: false },
    yaxis: { gridcolor: "#EEF0F3", zeroline: false },
  };
}
const PLOTLY_CONFIG = { displaylogo: false, responsive: true, modeBarButtonsToRemove: ["lasso2d", "select2d"] };
