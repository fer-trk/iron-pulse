// ── Auth guard: redirect to login if no token ──────────────────────────────
(function () {
  const publicPages = ["login.html"];
  const currentPage = window.location.pathname.split("/").pop() || "index.html";
  const isPublic = publicPages.some(p => currentPage.includes(p));

  if (!isPublic && !localStorage.getItem("access_token")) {
    window.location.href = "login.html";
  }
})();

// ── UI utilities ───────────────────────────────────────────────────────────
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-3 text-muted">Loading data...</p>
            </div>`;
    }
}

function showError(containerId, message = "Something went wrong.") {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>${message}
            </div>`;
    }
}

function showSuccess(message) {
    const alertContainer = document.getElementById("alert-container");
    if (alertContainer) {
        alertContainer.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="bi bi-check-circle-fill me-2"></i>${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount || 0);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('es-ES', options);
}

function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) form.reset();
}

(function () {
  function qs(selector, parent = document) {
    return parent.querySelector(selector);
  }

  function qsa(selector, parent = document) {
    return Array.from(parent.querySelectorAll(selector));
  }

  function setText(selectorOrId, value) {
    const element =
      document.getElementById(selectorOrId) || qs(selectorOrId);

    if (!element) return;

    element.textContent = value;
  }

  function setActiveNavigation() {
    const currentPage = window.location.pathname.split("/").pop() || "index.html";

    qsa(".navigation-menu .nav-link").forEach((link) => {
      const linkPage = link.getAttribute("href");

      link.classList.toggle("active", linkPage === currentPage);
    });
  }

  function setFormStatus(form, message, type = "muted") {
    const status = form.querySelector("[data-form-status]");

    if (!status) return;

    status.textContent = message;
    status.dataset.status = type;
  }

  function renderLoadingRow(tableBody, colspan, message = "Loading data...") {
    if (!tableBody) return;

    tableBody.innerHTML = `
      <tr>
        <td colspan="${colspan}" class="empty-table-message">
          ${message}
        </td>
      </tr>
    `;
  }

  function renderEmptyRow(tableBody, colspan, message = "No records loaded yet.") {
    if (!tableBody) return;

    tableBody.innerHTML = `
      <tr>
        <td colspan="${colspan}" class="empty-table-message">
          ${message}
        </td>
      </tr>
    `;
  }

  function renderErrorRow(tableBody, colspan, message = "Data unavailable.") {
    if (!tableBody) return;

    tableBody.innerHTML = `
      <tr>
        <td colspan="${colspan}" class="empty-table-message">
          ${message}
        </td>
      </tr>
    `;
  }

  function statusBadge(label, isActive = true) {
    return `
      <span class="status-badge ${isActive ? "" : "status-muted"}">
        ${escapeHtml(label)}
      </span>
    `;
  }

  function formatCurrency(value) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "EUR",
    }).format(Number(value || 0));
  }

  function formatDate(value) {
    if (!value) return "-";

    return new Date(value).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  function formatDateTime(value) {
    if (!value) return "-";

    return new Date(value).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function formatValue(value) {
    if (value === null || value === undefined || value === "") return "-";
    if (typeof value === "boolean") return value ? "Yes" : "No";

    return String(value);
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getAuthHeaders() {
    const token = localStorage.getItem("ironPulseToken");

    if (!token) return {};

    return {
      Authorization: `Bearer ${token}`,
    };
  }

  function showToast(message) {
    let toast = qs(".app-toast");

    if (!toast) {
      toast = document.createElement("div");
      toast.className = "app-toast";
      document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.add("is-visible");

    window.setTimeout(() => {
      toast.classList.remove("is-visible");
    }, 2500);
  }

  document.addEventListener("DOMContentLoaded", () => {
    setActiveNavigation();
  });

  window.IronPulseUI = {
    qs,
    qsa,
    setText,
    setActiveNavigation,
    setFormStatus,
    renderLoadingRow,
    renderEmptyRow,
    renderErrorRow,
    statusBadge,
    formatCurrency,
    formatDate,
    formatDateTime,
    formatValue,
    escapeHtml,
    getAuthHeaders,
    showToast,
  };
})();