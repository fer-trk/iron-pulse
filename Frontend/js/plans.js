let renderedRecords = new Map();
document.addEventListener("DOMContentLoaded", loadPlans);

async function loadPlans() {
    showLoading("plans-table-container");
    try {
        const plans = await getData("/plans/");
        renderPlansTable(plans);
    } catch (error) {
        console.error("Error loading plans:", error);
        showError("plans-table-container", "Could not load plans.");
    }
}

function renderPlansTable(plans) {
    renderedRecords = new Map((plans || []).map(r => [r.id, r]));
    const container = document.getElementById("plans-table-container");
    if (!plans || plans.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h5>No plans found</h5>
                <p>Add the first commercial plan to get started.</p>
            </div>`;
        return;
    }

    container.innerHTML = `
        <div class="table-responsive">
            <table class="table align-middle">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Price</th>
                        <th>Duration</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${plans.map(p => `
                        <tr>
                            <td>${p.id}</td>
                            <td class="fw-semibold">${escapeHtml(p.name)}</td>
                            <td>${escapeHtml(p.description || "-")}</td>
                            <td>${formatCurrency(p.price)}</td>
                            <td>${p.duration_days} days</td>
                            <td>${p.active
                                ? '<span class="badge badge-soft-success">Active</span>'
                                : '<span class="badge badge-soft-danger">Inactive</span>'
                            }</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary me-1"
                                    onclick="editRenderedRecord(${p.id})">
                                    <i class="bi bi-pencil"></i> Edit
                                </button>
                                <button class="btn btn-sm btn-outline-danger"
                                    onclick="deleteRenderedRecord(${p.id})">
                                    <i class="bi bi-trash"></i> Delete
                                </button>
                            </td>
                        </tr>`).join("")}
                </tbody>
            </table>
        </div>`;
}

// ── ADD ───────────────────────────────────────────────────────────────────
function openAddModal() {
    document.getElementById("add-form-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("addPlanModal")).show();
}

async function submitAddPlan() {
    const name        = document.getElementById("planName").value.trim();
    const description = document.getElementById("planDescription").value.trim();
    const price       = document.getElementById("planPrice").value;
    const duration    = document.getElementById("planDuration").value;
    const errorDiv    = document.getElementById("add-form-error");

    if (!name) { errorDiv.textContent = "Plan name is required."; errorDiv.classList.remove("d-none"); return; }
    if (!price || parseFloat(price) < 0) { errorDiv.textContent = "Please enter a valid price."; errorDiv.classList.remove("d-none"); return; }
    if (!duration || parseInt(duration) <= 0) { errorDiv.textContent = "Please enter a valid duration in days."; errorDiv.classList.remove("d-none"); return; }

    errorDiv.classList.add("d-none");

    try {
        await postData("/plans/", {
            name, description: description || null,
            price: parseFloat(price), duration_days: parseInt(duration), active: true
        });
        bootstrap.Modal.getInstance(document.getElementById("addPlanModal")).hide();
        showSuccess("Plan added successfully!");
        loadPlans();
    } catch (error) {
        errorDiv.textContent = "Could not save plan. Try again.";
        errorDiv.classList.remove("d-none");
    }
}

// ── EDIT ──────────────────────────────────────────────────────────────────
function openEditModal(id, name, description, price, duration, active) {
    document.getElementById("editPlanId").value          = id;
    document.getElementById("editPlanName").value        = name;
    document.getElementById("editPlanDescription").value = description;
    document.getElementById("editPlanPrice").value       = price;
    document.getElementById("editPlanDuration").value    = duration;
    document.getElementById("editPlanStatus").value      = active ? "true" : "false";
    document.getElementById("edit-form-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("editPlanModal")).show();
}

async function submitEditPlan() {
    const id          = document.getElementById("editPlanId").value;
    const name        = document.getElementById("editPlanName").value.trim();
    const description = document.getElementById("editPlanDescription").value.trim();
    const price       = document.getElementById("editPlanPrice").value;
    const duration    = document.getElementById("editPlanDuration").value;
    const active      = document.getElementById("editPlanStatus").value === "true";
    const errorDiv    = document.getElementById("edit-form-error");

    if (!name) { errorDiv.textContent = "Plan name is required."; errorDiv.classList.remove("d-none"); return; }
    if (!price || parseFloat(price) < 0) { errorDiv.textContent = "Please enter a valid price."; errorDiv.classList.remove("d-none"); return; }
    if (!duration || parseInt(duration) <= 0) { errorDiv.textContent = "Please enter a valid duration."; errorDiv.classList.remove("d-none"); return; }

    errorDiv.classList.add("d-none");

    try {
        await patchData(`/plans/${id}`, {
            name, description: description || null,
            price: parseFloat(price), duration_days: parseInt(duration), active
        });
        bootstrap.Modal.getInstance(document.getElementById("editPlanModal")).hide();
        showSuccess("Plan updated successfully!");
        loadPlans();
    } catch (error) {
        errorDiv.textContent = "Could not update plan. Try again.";
        errorDiv.classList.remove("d-none");
    }
}

// ── DELETE (físico) ───────────────────────────────────────────────────────
function confirmDelete(id, name) {
    document.getElementById("deletePlanName").textContent = name;
    document.getElementById("deletePlanId").value = id;
    document.getElementById("delete-plan-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("deletePlanModal")).show();
}

async function submitDeletePlan() {
    const id       = document.getElementById("deletePlanId").value;
    const errorDiv = document.getElementById("delete-plan-error");
    errorDiv.classList.add("d-none");

    try {
        await deleteData(`/plans/${id}`);
        bootstrap.Modal.getInstance(document.getElementById("deletePlanModal")).hide();
        showSuccess("Plan deleted successfully.");
        loadPlans();
    } catch (error) {
        errorDiv.textContent = error.message || "Could not delete plan. It may have memberships linked to it.";
        errorDiv.classList.remove("d-none");
    }
}

function editRenderedRecord(id) { const r = renderedRecords.get(id); if (r) openEditModal(...[r.id, r.name, r.description || "", r.price, r.duration_days, r.active]); }
function deleteRenderedRecord(id) { const r = renderedRecords.get(id); if (r) confirmDelete(r.id, r.name); }
