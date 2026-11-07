document.addEventListener("DOMContentLoaded", loadMembers);

async function loadMembers() {
    showLoading("members-table-container");
    try {
        const members = await getData("/members/");
        renderMembersTable(members);
    } catch (error) {
        console.error("Error loading members:", error);
        showError("members-table-container", "Could not load member data.");
    }
}

function renderMembersTable(members) {
    const container = document.getElementById("members-table-container");
    if (!members || members.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h5>No members found</h5>
                <p>Add the first member to get started.</p>
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
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${members.map(m => `
                        <tr>
                            <td>${m.id}</td>
                            <td class="fw-semibold">${m.first_name} ${m.last_name}</td>
                            <td>${m.email}</td>
                            <td>${m.phone || "-"}</td>
                            <td>
                                <span class="badge ${m.is_active ? 'badge-soft-success' : 'badge-soft-danger'}">
                                    ${m.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary me-1"
                                    onclick="openEditModal(${m.id}, '${m.first_name}', '${m.last_name}', '${m.email}', '${m.phone || ''}', ${m.is_active})">
                                    <i class="bi bi-pencil"></i> Edit
                                </button>
                                <button class="btn btn-sm btn-outline-danger"
                                    onclick="confirmDelete(${m.id}, '${m.first_name} ${m.last_name}')">
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
    document.getElementById("addMemberForm").reset();
    document.getElementById("add-form-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("addMemberModal")).show();
}

async function submitAddMember() {
    const firstName = document.getElementById("memberFirstName").value.trim();
    const lastName  = document.getElementById("memberLastName").value.trim();
    const email     = document.getElementById("memberEmail").value.trim();
    const phone     = document.getElementById("memberPhone").value.trim();
    const errorDiv  = document.getElementById("add-form-error");

    if (!firstName || !lastName) {
        errorDiv.textContent = "First name and last name are required.";
        errorDiv.classList.remove("d-none");
        return;
    }
    if (!email || !email.includes("@")) {
        errorDiv.textContent = "Please enter a valid email address.";
        errorDiv.classList.remove("d-none");
        return;
    }

    errorDiv.classList.add("d-none");

    try {
        await postData("/members/", {
            first_name: firstName, last_name: lastName,
            email, phone: phone || null, is_active: true
        });
        bootstrap.Modal.getInstance(document.getElementById("addMemberModal")).hide();
        showSuccess("Member added successfully!");
        loadMembers();
    } catch (error) {
        errorDiv.textContent = "Could not save member. Try again.";
        errorDiv.classList.remove("d-none");
    }
}

// ── EDIT ──────────────────────────────────────────────────────────────────
function openEditModal(id, firstName, lastName, email, phone, isActive) {
    document.getElementById("editMemberId").value        = id;
    document.getElementById("editMemberFirstName").value = firstName;
    document.getElementById("editMemberLastName").value  = lastName;
    document.getElementById("editMemberEmail").value     = email;
    document.getElementById("editMemberPhone").value     = phone;
    document.getElementById("editMemberStatus").value    = isActive ? "true" : "false";
    document.getElementById("edit-form-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("editMemberModal")).show();
}

async function submitEditMember() {
    const id        = document.getElementById("editMemberId").value;
    const firstName = document.getElementById("editMemberFirstName").value.trim();
    const lastName  = document.getElementById("editMemberLastName").value.trim();
    const email     = document.getElementById("editMemberEmail").value.trim();
    const phone     = document.getElementById("editMemberPhone").value.trim();
    const isActive  = document.getElementById("editMemberStatus").value === "true";
    const errorDiv  = document.getElementById("edit-form-error");

    if (!firstName || !lastName) {
        errorDiv.textContent = "First name and last name are required.";
        errorDiv.classList.remove("d-none");
        return;
    }
    if (!email || !email.includes("@")) {
        errorDiv.textContent = "Please enter a valid email address.";
        errorDiv.classList.remove("d-none");
        return;
    }

    errorDiv.classList.add("d-none");

    try {
        await patchData(`/members/${id}`, {
            first_name: firstName, last_name: lastName,
            email, phone: phone || null, is_active: isActive
        });
        bootstrap.Modal.getInstance(document.getElementById("editMemberModal")).hide();
        showSuccess("Member updated successfully!");
        loadMembers();
    } catch (error) {
        errorDiv.textContent = "Could not update member. Try again.";
        errorDiv.classList.remove("d-none");
    }
}

// ── DELETE (físico) ───────────────────────────────────────────────────────
function confirmDelete(id, name) {
    document.getElementById("deleteMemberName").textContent = name;
    document.getElementById("deleteMemberId").value = id;
    new bootstrap.Modal(document.getElementById("deleteMemberModal")).show();
}

async function submitDeleteMember() {
    const id       = document.getElementById("deleteMemberId").value;
    const errorDiv = document.getElementById("delete-form-error");
    errorDiv.classList.add("d-none");

    try {
        await deleteData(`/members/${id}`);
        bootstrap.Modal.getInstance(document.getElementById("deleteMemberModal")).hide();
        showSuccess("Member deleted successfully.");
        loadMembers();
    } catch (error) {
        // Mostrar error en el modal (p.ej. "Cannot delete a member with an active membership")
        errorDiv.textContent = error.message || "Could not delete member. Try again.";
        errorDiv.classList.remove("d-none");
    }
}