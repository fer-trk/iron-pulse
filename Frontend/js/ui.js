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

// Highlight the current page in the shared navigation.
document.addEventListener("DOMContentLoaded", () => {
  const currentPage = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".navigation-menu .nav-link").forEach((link) => {
    link.classList.toggle("active", link.getAttribute("href") === currentPage);
  });
});

function escapeHtml(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}
