document.addEventListener("DOMContentLoaded", loadMemberships);

// Cache de members para mostrar nombres en la tabla
let membersMap = {};
let existingMemberships = [];

async function loadMemberships() {
  showLoading("memberships-table-container");
  try {
    // Carga memberships y members en paralelo
    const [memberships, members] = await Promise.all([
      getData("/memberships/"),
      getData("/members/")
    ]);

    // Construye un mapa id → nombre
    membersMap = {};
    (members || []).forEach(m => {
      membersMap[m.id] = `${m.first_name} ${m.last_name}`;
    });

    existingMemberships = memberships || [];
    renderMembershipsTable(existingMemberships);
  } catch (error) {
    console.error("Error loading memberships:", error);
    showError("memberships-table-container", "Could not load memberships.");
  }
}

function getMemberName(memberId) {
  return membersMap[memberId] || `Member ${memberId}`;
}

function renderMembershipsTable(memberships) {
  const container = document.getElementById("memberships-table-container");

  if (!memberships || memberships.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <h5>No memberships found</h5>
        <p>Create the first membership to link a member with a plan.</p>
      </div>`;
    return;
  }

  container.innerHTML = `
    <div class="table-responsive">
      <table class="table align-middle">
        <thead>
          <tr>
            <th>ID</th>
            <th>Member</th>
            <th>Plan</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${memberships.map(m => `
            <tr>
              <td>${m.id}</td>
              <td class="fw-semibold">${getMemberName(m.member_id)}</td>
              <td>${getPlanName(m.plan_id)}</td>
              <td>${formatDate(m.start_date)}</td>
              <td>${formatDate(m.end_date)}</td>
              <td>${renderMembershipBadge(m.status)}</td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditModal(${m.id}, '${m.status}')">
                  <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="confirmDeleteMembership(${m.id})">
                  <i class="bi bi-trash"></i> Delete
                </button>
              </td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

function getPlanName(planId) {
  const names = { 1: "Mensual", 2: "Semestral", 3: "Anual" };
  return names[planId] || `Plan ${planId}`;
}

function renderMembershipBadge(status) {
  if (status === "active")    return `<span class="badge badge-soft-success">Active</span>`;
  if (status === "pending")   return `<span class="badge badge-soft-warning">Pending</span>`;
  if (status === "expired")   return `<span class="badge badge-soft-danger">Expired</span>`;
  if (status === "cancelled") return `<span class="badge badge-soft-danger">Cancelled</span>`;
  return `<span class="badge badge-soft-warning">${status}</span>`;
}

// ── Calcula fecha de fin ───────────────────────────────────────────────────
function calculateEndDate() {
  const planSelect     = document.getElementById("membershipPlanId");
  const selectedOption = planSelect.options[planSelect.selectedIndex];
  const duration       = selectedOption ? parseInt(selectedOption.getAttribute("data-duration")) : null;
  const startDate      = document.getElementById("membershipStartDate").value;
  const endDateField   = document.getElementById("planInfoEndDate");

  if (duration && startDate) {
    const end = new Date(startDate);
    end.setDate(end.getDate() + duration);
    endDateField.value = end.toLocaleDateString("es-ES", { year: "numeric", month: "short", day: "numeric" });
  } else {
    endDateField.value = "";
  }
}

// ── ADD ───────────────────────────────────────────────────────────────────
async function openAddModal() {
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("membershipStartDate").value = today;
  document.getElementById("add-form-error").classList.add("d-none");
  document.getElementById("planInfoPrice").value    = "";
  document.getElementById("planInfoDuration").value = "";
  document.getElementById("planInfoEndDate").value  = "";
  document.getElementById("membershipPlanId").selectedIndex = 0;

  const memberSelect = document.getElementById("membershipMemberId");
  memberSelect.innerHTML = `<option value="">Loading members...</option>`;

  try {
    const members = await getData("/members/");
    memberSelect.innerHTML = members && members.length
      ? `<option value="">Select a member...</option>` +
        members.map(m => {
          const hasActive = existingMemberships.find(
            ms => ms.member_id === m.id && ["active", "pending"].includes(ms.status)
          );
          const label = hasActive
            ? `${m.id} — ${m.first_name} ${m.last_name} ⚠ already has membership`
            : `${m.id} — ${m.first_name} ${m.last_name}`;
          return `<option value="${m.id}" ${hasActive ? 'disabled style="color:#888"' : ""}>${label}</option>`;
        }).join("")
      : `<option value="">No members found</option>`;
  } catch {
    memberSelect.innerHTML = `<option value="">Could not load members</option>`;
  }

  new bootstrap.Modal(document.getElementById("addMembershipModal")).show();
}

function onPlanSelected() {
  const planSelect     = document.getElementById("membershipPlanId");
  const selectedOption = planSelect.options[planSelect.selectedIndex];
  const price          = selectedOption.getAttribute("data-price");
  const duration       = selectedOption.getAttribute("data-duration");

  if (price && duration && planSelect.value !== "") {
    document.getElementById("planInfoPrice").value    = `€ ${parseFloat(price).toFixed(2)}`;
    document.getElementById("planInfoDuration").value = `${duration} days`;
  } else {
    document.getElementById("planInfoPrice").value    = "";
    document.getElementById("planInfoDuration").value = "";
  }
  calculateEndDate();
}

function onStartDateChanged() { calculateEndDate(); }

async function submitAddMembership() {
  const memberId  = document.getElementById("membershipMemberId").value;
  const planId    = document.getElementById("membershipPlanId").value;
  const startDate = document.getElementById("membershipStartDate").value;
  const status    = document.getElementById("membershipStatus").value;
  const errorDiv  = document.getElementById("add-form-error");

  if (!memberId) { errorDiv.textContent = "Please select a member."; errorDiv.classList.remove("d-none"); return; }
  if (!planId)   { errorDiv.textContent = "Please select a plan.";   errorDiv.classList.remove("d-none"); return; }
  if (!startDate){ errorDiv.textContent = "Start date is required."; errorDiv.classList.remove("d-none"); return; }

  const alreadyHas = existingMemberships.find(
    m => m.member_id === parseInt(memberId) && ["active", "pending"].includes(m.status)
  );
  if (alreadyHas) {
    errorDiv.textContent = `This member already has an active or pending membership (ID: ${alreadyHas.id}).`;
    errorDiv.classList.remove("d-none");
    return;
  }

  errorDiv.classList.add("d-none");

  try {
    await postData("/memberships/", {
      member_id: parseInt(memberId), plan_id: parseInt(planId),
      start_date: startDate, status
    });
    bootstrap.Modal.getInstance(document.getElementById("addMembershipModal")).hide();
    showSuccess("Membership created successfully!");
    loadMemberships();
  } catch (error) {
    errorDiv.textContent = error.message || "Could not save membership. Try again.";
    errorDiv.classList.remove("d-none");
  }
}

// ── EDIT ──────────────────────────────────────────────────────────────────
function openEditModal(id, currentStatus) {
  document.getElementById("editMembershipId").value     = id;
  document.getElementById("editMembershipStatus").value = currentStatus;
  document.getElementById("edit-form-error").classList.add("d-none");
  new bootstrap.Modal(document.getElementById("editMembershipModal")).show();
}

async function submitEditMembership() {
  const id       = document.getElementById("editMembershipId").value;
  const status   = document.getElementById("editMembershipStatus").value;
  const errorDiv = document.getElementById("edit-form-error");
  errorDiv.classList.add("d-none");
  try {
    await patchData(`/memberships/${id}`, { status });
    bootstrap.Modal.getInstance(document.getElementById("editMembershipModal")).hide();
    showSuccess("Membership updated successfully!");
    loadMemberships();
  } catch (error) {
    errorDiv.textContent = error.message || "Could not update membership. Try again.";
    errorDiv.classList.remove("d-none");
  }
}

// ── DELETE (físico) ───────────────────────────────────────────────────────
function confirmDeleteMembership(id) {
  document.getElementById("deleteMembershipId").value = id;
  document.getElementById("delete-membership-error").classList.add("d-none");
  new bootstrap.Modal(document.getElementById("deleteMembershipModal")).show();
}

async function submitDeleteMembership() {
  const id       = document.getElementById("deleteMembershipId").value;
  const errorDiv = document.getElementById("delete-membership-error");
  errorDiv.classList.add("d-none");

  try {
    await deleteData(`/memberships/${id}`);
    bootstrap.Modal.getInstance(document.getElementById("deleteMembershipModal")).hide();
    showSuccess("Membership deleted successfully.");
    loadMemberships();
  } catch (error) {
    errorDiv.textContent = error.message || "Could not delete membership. It may have completed payments linked.";
    errorDiv.classList.remove("d-none");
  }
}