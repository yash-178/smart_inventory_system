/* reports.js */

async function downloadReport(format, statusElId, btnId) {
  const statusEl = document.getElementById(statusElId);
  const btn = document.getElementById(btnId);
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Generating…";
  statusEl.innerHTML = "";

  try {
    const res = await fetch(`/api/reports/generate?format=${format}`);
    if (!res.ok) {
      let message = `Request failed (${res.status})`;
      try {
        const payload = await res.json();
        message = payload.error || message;
      } catch (_) { /* response wasn't JSON (i.e. it was the file) */ }
      throw new Error(message);
    }
    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `inventory_report.${format}`;

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    showToast(`${filename} downloaded.`, "success");
  } catch (err) {
    statusEl.innerHTML = `<div class="alert-banner alert-banner--danger" style="margin-top:12px;">Could not generate report: ${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("download-pdf-btn").addEventListener("click", () => downloadReport("pdf", "pdf-status", "download-pdf-btn"));
  document.getElementById("download-csv-btn").addEventListener("click", () => downloadReport("csv", "csv-status", "download-csv-btn"));
});
