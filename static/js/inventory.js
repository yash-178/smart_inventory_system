/* inventory.js */

const invState = {
  search: "",
  category: "all",
  status: "all",
  supplier: "all",
  sort_by: "product_name",
  order: "asc",
  page: 1,
  page_size: 20,
};

function buildQuery(state) {
  const params = new URLSearchParams();
  Object.entries(state).forEach(([k, v]) => params.set(k, v));
  return params.toString();
}

function renderInventoryRows(items) {
  const tbody = document.getElementById("inventory-tbody");
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty-state">No products match your filters. Try widening your search.</td></tr>`;
    return;
  }
  tbody.innerHTML = items.map((p) => `
    <tr>
      <td class="mono">${escapeHtml(p.product_id)}</td>
      <td>${escapeHtml(p.product_name)}</td>
      <td>${escapeHtml(p.category)}</td>
      <td>${escapeHtml(p.supplier)}</td>
      <td class="mono">${formatNumber(p.stock_quantity)}</td>
      <td class="mono">${formatNumber(p.reorder_level)}</td>
      <td class="mono">${formatCurrency(p.unit_price)}</td>
      <td class="mono">${formatCurrency(p.inventory_value)}</td>
      <td><span class="badge ${statusBadgeClass(p.status)}">${escapeHtml(p.status)}</span></td>
    </tr>
  `).join("");
}

function updateSortHeaders() {
  document.querySelectorAll("th.sortable").forEach((th) => {
    th.querySelector(".sort-arrow")?.remove();
    if (th.dataset.sort === invState.sort_by) {
      const arrow = document.createElement("span");
      arrow.className = "sort-arrow";
      arrow.textContent = invState.order === "asc" ? "▲" : "▼";
      th.appendChild(arrow);
    }
  });
}

async function loadInventory() {
  const tbody = document.getElementById("inventory-tbody");
  tbody.innerHTML = `<tr><td colspan="9" class="loading-state">Loading inventory…</td></tr>`;
  try {
    const data = await API.get(`/api/inventory?${buildQuery(invState)}`);
    renderInventoryRows(data.items);

    document.getElementById("pagination-summary").textContent =
      data.total_items === 0
        ? "0 results"
        : `Showing ${(data.page - 1) * data.page_size + 1}–${Math.min(data.page * data.page_size, data.total_items)} of ${data.total_items}`;
    document.getElementById("page-indicator").textContent = `Page ${data.page} / ${data.total_pages}`;
    document.getElementById("prev-page").disabled = data.page <= 1;
    document.getElementById("next-page").disabled = data.page >= data.total_pages;
    invState.page = data.page;
    updateSortHeaders();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" class="error-state">Could not load inventory: ${escapeHtml(err.message)}</td></tr>`;
  }
}

async function loadFilterOptions() {
  try {
    const filters = await API.get("/api/inventory/filters");
    const catSel = document.getElementById("category-filter");
    filters.categories.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c; opt.textContent = c;
      catSel.appendChild(opt);
    });
    const supSel = document.getElementById("supplier-filter");
    filters.suppliers.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s; opt.textContent = s;
      supSel.appendChild(opt);
    });
  } catch (err) {
    showToast(`Could not load filter options: ${err.message}`, "error");
  }
}

function wireInventoryControls() {
  document.getElementById("search-input").addEventListener("input", debounce((e) => {
    invState.search = e.target.value;
    invState.page = 1;
    loadInventory();
  }, 350));

  document.getElementById("category-filter").addEventListener("change", (e) => {
    invState.category = e.target.value; invState.page = 1; loadInventory();
  });
  document.getElementById("status-filter").addEventListener("change", (e) => {
    invState.status = e.target.value; invState.page = 1; loadInventory();
  });
  document.getElementById("supplier-filter").addEventListener("change", (e) => {
    invState.supplier = e.target.value; invState.page = 1; loadInventory();
  });
  document.getElementById("page-size-select").addEventListener("change", (e) => {
    invState.page_size = Number(e.target.value); invState.page = 1; loadInventory();
  });

  document.getElementById("prev-page").addEventListener("click", () => {
    if (invState.page > 1) { invState.page -= 1; loadInventory(); }
  });
  document.getElementById("next-page").addEventListener("click", () => {
    invState.page += 1; loadInventory();
  });

  document.querySelectorAll("th.sortable").forEach((th) => {
    th.addEventListener("click", () => {
      const col = th.dataset.sort;
      if (invState.sort_by === col) {
        invState.order = invState.order === "asc" ? "desc" : "asc";
      } else {
        invState.sort_by = col;
        invState.order = "asc";
      }
      invState.page = 1;
      loadInventory();
    });
  });
}

function initInventoryPage() {
  loadFilterOptions();
  wireInventoryControls();
  loadInventory();
}

window.onDataReloaded = initInventoryPage;
document.addEventListener("DOMContentLoaded", initInventoryPage);
