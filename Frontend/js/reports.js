document.addEventListener("DOMContentLoaded", () => {
    // Usar fecha local (no UTC) para evitar desfase de zona horaria
    const now = new Date();
    const localDate = (d) => {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, "0");
        const day = String(d.getDate()).padStart(2, "0");
        return `${y}-${m}-${day}`;
    };

    const today = localDate(now);
    const thirtyDaysAgo = new Date(now);
    thirtyDaysAgo.setDate(now.getDate() - 30);

    document.getElementById("endDate").value   = today;
    document.getElementById("startDate").value = localDate(thirtyDaysAgo);

    loadAllReports();
});

async function loadAllReports() {
    const startDate = document.getElementById("startDate").value;
    const endDate   = document.getElementById("endDate").value;

    if (startDate && endDate && startDate > endDate) {
        showError("alert-container", "Start date cannot be after end date.");
        return;
    }

    const params = startDate && endDate ? `?start_date=${startDate}&end_date=${endDate}` : "";

    await Promise.all([
        loadIncomeReport(params),
        loadAttendanceSummary(params),
        loadAttendanceByMember(params),
        loadAttendanceByShift(params)
    ]);
}

// ── Income ────────────────────────────────────────────────────────────────
async function loadIncomeReport(params) {
    const incomeEl   = document.getElementById("kpi-income");
    const paymentsEl = document.getElementById("kpi-payments");

    incomeEl.textContent   = "Loading...";
    paymentsEl.textContent = "Loading...";

    try {
        const data = await getData(`/reports/income${params}`);
        incomeEl.textContent   = formatCurrency(data.total_income);
        paymentsEl.textContent = data.total_payments;
    } catch (error) {
        console.error("Error loading income report:", error);
        incomeEl.textContent   = "—";
        paymentsEl.textContent = "—";
    }
}

// ── Attendance summary ────────────────────────────────────────────────────
async function loadAttendanceSummary(params) {
    ["kpi-total-att", "kpi-checkins", "kpi-checkouts", "kpi-inside"].forEach(id => {
        document.getElementById(id).textContent = "Loading...";
    });

    try {
        const data = await getData(`/reports/attendance${params}`);
        document.getElementById("kpi-total-att").textContent = data.total_attendances;
        document.getElementById("kpi-checkins").textContent  = data.total_check_ins;
        document.getElementById("kpi-checkouts").textContent = data.total_check_outs;
        document.getElementById("kpi-inside").textContent   = data.current_people_inside;
    } catch (error) {
        console.error("Error loading attendance summary:", error);
        ["kpi-total-att", "kpi-checkins", "kpi-checkouts", "kpi-inside"].forEach(id => {
            document.getElementById(id).textContent = "—";
        });
    }
}

// ── Attendance by member ──────────────────────────────────────────────────
async function loadAttendanceByMember(params) {
    showLoading("attendance-by-member-container");
    try {
        const data = await getData(`/reports/attendance/by-member${params}`);

        if (!data || data.length === 0) {
            document.getElementById("attendance-by-member-container").innerHTML = `
                <div class="empty-state">
                    <h5>No data available</h5>
                    <p>No attendance records found for the selected period.</p>
                </div>`;
            return;
        }

        document.getElementById("attendance-by-member-container").innerHTML = `
            <div class="table-responsive">
                <table class="table align-middle">
                    <thead>
                        <tr>
                            <th>Member ID</th>
                            <th>Name</th>
                            <th>Total Attendances</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(r => `
                            <tr>
                                <td>${r.member_id}</td>
                                <td class="fw-semibold">${r.first_name} ${r.last_name}</td>
                                <td><span class="badge badge-soft-success">${r.total_attendances}</span></td>
                            </tr>`).join("")}
                    </tbody>
                </table>
            </div>`;
    } catch (error) {
        console.error("Error loading attendance by member:", error);
        showError("attendance-by-member-container", "Could not load attendance by member.");
    }
}

// ── Attendance by shift ───────────────────────────────────────────────────
async function loadAttendanceByShift(params) {
    showLoading("attendance-by-shift-container");
    try {
        const data = await getData(`/reports/attendance/by-shift${params}`);

        if (!data || data.length === 0) {
            document.getElementById("attendance-by-shift-container").innerHTML = `
                <div class="empty-state">
                    <h5>No data available</h5>
                    <p>No attendance records linked to shifts found for the selected period.</p>
                </div>`;
            return;
        }

        document.getElementById("attendance-by-shift-container").innerHTML = `
            <div class="table-responsive">
                <table class="table align-middle">
                    <thead>
                        <tr>
                            <th>Shift ID</th>
                            <th>Date</th>
                            <th>Total Attendances</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(r => `
                            <tr>
                                <td>${r.shift_id}</td>
                                <td>${formatDate(r.reservation_date)}</td>
                                <td><span class="badge badge-soft-success">${r.total_attendances}</span></td>
                            </tr>`).join("")}
                    </tbody>
                </table>
            </div>`;
    } catch (error) {
        console.error("Error loading attendance by shift:", error);
        showError("attendance-by-shift-container", "Could not load attendance by shift.");
    }
}