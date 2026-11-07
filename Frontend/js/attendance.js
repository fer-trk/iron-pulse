document.addEventListener("DOMContentLoaded", loadAttendance);

async function loadAttendance() {
    showLoading("attendance-table-container");
    try {
        const records = await getData("/attendances/");
        renderAttendanceTable(records);
    } catch (error) {
        console.error("Error loading attendance:", error);
        showError("attendance-table-container", "Could not load attendance records.");
    }
}

function renderAttendanceTable(records) {
    const container = document.getElementById("attendance-table-container");

    if (!records || records.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h5>No attendance records found</h5>
                <p>No check-ins have been registered yet.</p>
            </div>`;
        return;
    }

    container.innerHTML = `
        <div class="table-responsive">
            <table class="table align-middle">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Member ID</th>
                        <th>Reservation ID</th>
                        <th>Check In</th>
                        <th>Check Out</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${records.map(r => `
                        <tr>
                            <td>${r.id}</td>
                            <td>${r.member_id}</td>
                            <td>${r.reservation_id}</td>
                            <td>${formatDate(r.check_in)}</td>
                            <td>${r.check_out ? formatDate(r.check_out) : "-"}</td>
                            <td>${r.check_out
                                ? '<span class="badge badge-soft-success">Completed</span>'
                                : '<span class="badge badge-soft-warning">On-site</span>'
                            }</td>
                        </tr>`).join("")}
                </tbody>
            </table>
        </div>`;
}

// ── ADD ───────────────────────────────────────────────────────────────────
async function openAddModal() {
    document.getElementById("form-error").classList.add("d-none");

    // Cargar miembros en el select
    const memberSelect = document.getElementById("attendanceMemberId");
    memberSelect.innerHTML = `<option value="">Loading members...</option>`;

    try {
        const members = await getData("/members/");
        if (members && members.length) {
            memberSelect.innerHTML = `<option value="">Select a member...</option>` +
                members
                    .filter(m => m.is_active)
                    .map(m => `<option value="${m.id}">${m.id} — ${m.first_name} ${m.last_name}</option>`)
                    .join("");
        } else {
            memberSelect.innerHTML = `<option value="">No active members found</option>`;
        }
    } catch {
        memberSelect.innerHTML = `<option value="">Could not load members</option>`;
    }

    new bootstrap.Modal(document.getElementById("addAttendanceModal")).show();
}

async function submitAddAttendance() {
    const memberId      = document.getElementById("attendanceMemberId").value;
    const reservationId = document.getElementById("attendanceReservationId").value;
    const errorDiv      = document.getElementById("form-error");

    if (!memberId) {
        errorDiv.textContent = "Please select a member.";
        errorDiv.classList.remove("d-none");
        return;
    }
    if (!reservationId) {
        errorDiv.textContent = "Reservation ID is required.";
        errorDiv.classList.remove("d-none");
        return;
    }

    errorDiv.classList.add("d-none");

    try {
        await postData("/attendances/", {
            member_id:      parseInt(memberId),
            reservation_id: parseInt(reservationId)
        });
        bootstrap.Modal.getInstance(document.getElementById("addAttendanceModal")).hide();
        showSuccess("Attendance registered successfully!");
        loadAttendance();
    } catch (error) {
        console.error("Error registering attendance:", error);
        errorDiv.textContent = error.message || "Could not register attendance. Check that the reservation exists, belongs to this member and is confirmed.";
        errorDiv.classList.remove("d-none");
    }
}