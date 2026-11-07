document.addEventListener("DOMContentLoaded", loadPayments);

const PLAN_PRICES = { 1: 30, 2: 150, 3: 270 };
const PLAN_NAMES  = { 1: "Mensual", 2: "Semestral", 3: "Anual" };

// Cache de members para mostrar nombres
let membersMap = {};

async function loadPayments() {
    showLoading("payments-table-container");
    try {
        const [payments, members] = await Promise.all([
            getData("/payments/"),
            getData("/members/")
        ]);

        // Construye mapa membership_id → member_name via memberships
        const memberships = await getData("/memberships/");
        const membershipMemberMap = {};
        (memberships || []).forEach(ms => {
            const member = (members || []).find(m => m.id === ms.member_id);
            if (member) {
                membershipMemberMap[ms.id] = `${member.first_name} ${member.last_name}`;
            }
        });

        // Guarda también el mapa de members por id para el modal
        membersMap = {};
        (members || []).forEach(m => { membersMap[m.id] = `${m.first_name} ${m.last_name}`; });

        renderPaymentsTable(payments, membershipMemberMap);
    } catch (error) {
        console.error("Error loading payments:", error);
        showError("payments-table-container", "Failed to fetch payment records.");
    }
}

function renderPaymentsTable(payments, membershipMemberMap = {}) {
    const container = document.getElementById("payments-table-container");

    if (!payments || payments.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h5>No payments found</h5>
                <p>No payment records available yet.</p>
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
                        <th>Membership</th>
                        <th>Amount</th>
                        <th>Date</th>
                        <th>Method</th>
                        <th>Reference</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${payments.map(p => `
                        <tr>
                            <td>${p.id}</td>
                            <td class="fw-semibold">${membershipMemberMap[p.membership_id] || "-"}</td>
                            <td>${p.membership_id}</td>
                            <td>${formatCurrency(p.amount)}</td>
                            <td>${formatDate(p.payment_date)}</td>
                            <td class="text-capitalize">${p.payment_method || "-"}</td>
                            <td>${p.reference || "-"}</td>
                            <td>${renderPaymentBadge(p.status)}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary me-1"
                                    onclick="openEditModal(${p.id}, '${p.status}', '${p.reference || ''}', '${p.notes || ''}')">
                                    <i class="bi bi-pencil"></i> Edit
                                </button>
                                <button class="btn btn-sm btn-outline-danger"
                                    onclick="confirmDeletePayment(${p.id})">
                                    <i class="bi bi-trash"></i> Delete
                                </button>
                            </td>
                        </tr>`).join("")}
                </tbody>
            </table>
        </div>`;
}

function renderPaymentBadge(status) {
    if (status === "completed") return `<span class="badge badge-soft-success">Completed</span>`;
    if (status === "pending")   return `<span class="badge badge-soft-warning">Pending</span>`;
    if (status === "refunded")  return `<span class="badge badge-soft-warning">Refunded</span>`;
    return `<span class="badge badge-soft-danger">Failed</span>`;
}

// ── ADD ───────────────────────────────────────────────────────────────────
async function openAddModal() {
    document.getElementById("form-error").classList.add("d-none");
    document.getElementById("paymentAmount").value = "";
    document.getElementById("paymentAmount").readOnly = false;
    document.getElementById("paymentAmount").classList.remove("bg-light");

    const membershipSelect = document.getElementById("paymentMembershipId");
    membershipSelect.innerHTML = `<option value="">Loading memberships...</option>`;

    try {
        const [memberships, members] = await Promise.all([
            getData("/memberships/"),
            getData("/members/")
        ]);

        // Mapa member_id → nombre
        const mMap = {};
        (members || []).forEach(m => { mMap[m.id] = `${m.first_name} ${m.last_name}`; });

        const active = (memberships || []).filter(m => ["active", "pending"].includes(m.status));

        if (!active.length) {
            membershipSelect.innerHTML = `<option value="">No active memberships found</option>`;
        } else {
            membershipSelect.innerHTML = `<option value="">Select a membership...</option>` +
                active.map(ms => {
                    const memberName = mMap[ms.member_id] || `Member ${ms.member_id}`;
                    const planName   = PLAN_NAMES[ms.plan_id] || `Plan ${ms.plan_id}`;
                    const price      = PLAN_PRICES[ms.plan_id] || "";
                    return `<option value="${ms.id}" data-price="${price}">
                        #${ms.id} — ${memberName} · ${planName}${price ? ` (€${price})` : ""}
                    </option>`;
                }).join("");
        }
    } catch {
        membershipSelect.innerHTML = `<option value="">Could not load memberships</option>`;
    }

    new bootstrap.Modal(document.getElementById("addPaymentModal")).show();
}

function onMembershipSelected() {
    const select         = document.getElementById("paymentMembershipId");
    const selectedOption = select.options[select.selectedIndex];
    const price          = selectedOption.getAttribute("data-price");
    const amountField    = document.getElementById("paymentAmount");

    if (price && select.value !== "") {
        amountField.value    = parseFloat(price).toFixed(2);
        amountField.readOnly = true;
        amountField.classList.add("bg-light");
    } else {
        amountField.value    = "";
        amountField.readOnly = false;
        amountField.classList.remove("bg-light");
    }
}

async function submitAddPayment() {
    const membershipId = document.getElementById("paymentMembershipId").value;
    const amount       = document.getElementById("paymentAmount").value;
    const method       = document.getElementById("paymentMethod").value;
    const status       = document.getElementById("paymentStatus").value;
    const reference    = document.getElementById("paymentReference").value.trim();
    const notes        = document.getElementById("paymentNotes").value.trim();
    const errorDiv     = document.getElementById("form-error");

    if (!membershipId) {
        errorDiv.textContent = "Please select a membership.";
        errorDiv.classList.remove("d-none");
        return;
    }
    if (!amount || parseFloat(amount) <= 0) {
        errorDiv.textContent = "Amount must be greater than 0.";
        errorDiv.classList.remove("d-none");
        return;
    }

    errorDiv.classList.add("d-none");

    try {
        await postData("/payments/", {
            membership_id:  parseInt(membershipId),
            amount:         parseFloat(amount),
            payment_method: method,
            status, reference, notes
        });
        bootstrap.Modal.getInstance(document.getElementById("addPaymentModal")).hide();
        document.getElementById("paymentAmount").readOnly = false;
        document.getElementById("paymentAmount").classList.remove("bg-light");
        showSuccess("Payment registered successfully!");
        loadPayments();
    } catch (error) {
        errorDiv.textContent = error.message || "Could not save payment. Try again.";
        errorDiv.classList.remove("d-none");
    }
}

// ── EDIT ──────────────────────────────────────────────────────────────────
function openEditModal(id, status, reference, notes) {
    document.getElementById("editPaymentId").value        = id;
    document.getElementById("editPaymentStatus").value    = status;
    document.getElementById("editPaymentReference").value = reference;
    document.getElementById("editPaymentNotes").value     = notes;
    document.getElementById("edit-payment-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("editPaymentModal")).show();
}

async function submitEditPayment() {
    const id        = document.getElementById("editPaymentId").value;
    const status    = document.getElementById("editPaymentStatus").value;
    const reference = document.getElementById("editPaymentReference").value.trim();
    const notes     = document.getElementById("editPaymentNotes").value.trim();
    const errorDiv  = document.getElementById("edit-payment-error");
    errorDiv.classList.add("d-none");

    try {
        await patchData(`/payments/${id}`, { status, reference, notes });
        bootstrap.Modal.getInstance(document.getElementById("editPaymentModal")).hide();
        showSuccess("Payment updated successfully!");
        loadPayments();
    } catch (error) {
        errorDiv.textContent = error.message || "Could not update payment. Try again.";
        errorDiv.classList.remove("d-none");
    }
}

// ── DELETE ────────────────────────────────────────────────────────────────
function confirmDeletePayment(id) {
    document.getElementById("deletePaymentId").value = id;
    document.getElementById("delete-payment-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("deletePaymentModal")).show();
}

async function submitDeletePayment() {
    const id       = document.getElementById("deletePaymentId").value;
    const errorDiv = document.getElementById("delete-payment-error");
    errorDiv.classList.add("d-none");

    try {
        await deleteData(`/payments/${id}`);
        bootstrap.Modal.getInstance(document.getElementById("deletePaymentModal")).hide();
        showSuccess("Payment deleted successfully.");
        loadPayments();
    } catch (error) {
        errorDiv.textContent = error.message || "Could not delete payment.";
        errorDiv.classList.remove("d-none");
    }
}