//const API_BASE_URL = "http://localhost:8000/api/v1";
const API_BASE_URL = "/api/v1";

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
});

async function loadDashboard() {
  setLiveStatus("Loading");

  try {
    const [members, classes, payments, attendances] = await Promise.all([
      fetchData("/members/?is_active=true&limit=100"),
      fetchData("/shifts/"),
      fetchData("/payments/?limit=100"),
      fetchData("/attendances/?limit=100"),
    ]);

    renderMembersKpi(members);
    renderClassesKpi(classes);
    renderPaymentsKpi(payments);
    renderAttendanceKpi(attendances);
    renderHeroPanel(classes);
    renderScheduleTable(classes);

    setLiveStatus("Ready");
  } catch (error) {
    console.error("Dashboard error:", error);
    setLiveStatus("API unavailable");
  }
}

async function fetchData(endpoint) {
  const token = localStorage.getItem("ironPulseToken");

  const headers = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

function renderMembersKpi(members) {
  updateKpiCard(0, {
    value: members.length || "No data",
    note: members.length
      ? "Active members currently registered"
      : "Members have not been loaded yet",
  });
}

function renderClassesKpi(classes) {
  const todayClasses = getTodayClasses(classes);

  updateKpiCard(1, {
    value: todayClasses.length || "No data",
    note: todayClasses.length
      ? "Classes scheduled for today"
      : "Classes have not been loaded yet",
  });
}

function renderPaymentsKpi(payments) {
  const monthlyRevenue = payments
    .filter((payment) => payment.status === "completed")
    .filter((payment) => isCurrentMonth(payment.payment_date))
    .reduce((total, payment) => total + Number(payment.amount || 0), 0);

  updateKpiCard(2, {
    value: monthlyRevenue ? formatCurrency(monthlyRevenue) : "No data",
    note: monthlyRevenue
      ? "Completed payments this month"
      : "Payments have not been loaded yet",
  });
}

function renderAttendanceKpi(attendances) {
  const todayAttendances = attendances.filter((attendance) =>
    isToday(attendance.check_in)
  );

  updateKpiCard(3, {
    value: todayAttendances.length || "No data",
    note: todayAttendances.length
      ? "Check-ins registered today"
      : "Attendance has not been registered yet",
  });
}

function renderHeroPanel(classes) {
  const todayClasses = getTodayClasses(classes);
  const metricNumber = document.querySelector(".metric-number");
  const metricText = document.querySelector(".metric-text");
  const classList = document.querySelector(".hero-class-list");

  if (!metricNumber || !metricText || !classList) return;

  if (!todayClasses.length) {
    metricNumber.textContent = "No data";
    metricText.textContent = "No classes loaded for today";

    classList.innerHTML = `
      <article class="hero-class-card empty-state-card">
        <div>
          <h2>No classes yet</h2>
          <p>Classes will appear here when they are created.</p>
        </div>
        <span class="status-badge status-muted">Pending</span>
      </article>
    `;

    return;
  }

  metricNumber.textContent = todayClasses.length;
  metricText.textContent = "Classes scheduled for today";

  classList.innerHTML = todayClasses.slice(0, 3).map((gymClass) => `
    <article class="hero-class-card">
      <div>
        <h2>${gymClass.class_name}</h2>
        <p>${gymClass.start_time} - ${gymClass.end_time} · ${gymClass.instructor}</p>
      </div>
      <span class="status-badge">
        ${gymClass.active_slot ? "Active" : "Paused"}
      </span>
    </article>
  `).join("");
}

function renderScheduleTable(classes) {
  const tableBody = document.querySelector(".dashboard-table tbody");
  const todayClasses = getTodayClasses(classes);

  if (!tableBody) return;

  if (!todayClasses.length) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-table-message">
          No classes have been loaded yet.
        </td>
      </tr>
    `;

    return;
  }

  tableBody.innerHTML = todayClasses.map((gymClass) => `
    <tr>
      <td>${gymClass.class_name}</td>
      <td>${gymClass.start_time} - ${gymClass.end_time}</td>
      <td>${gymClass.instructor}</td>
      <td>${gymClass.max_capacity}</td>
      <td>
        <span class="status-badge ${gymClass.active_slot ? "" : "status-muted"}">
          ${gymClass.active_slot ? "Active" : "Paused"}
        </span>
      </td>
    </tr>
  `).join("");
}

function updateKpiCard(index, data) {
  const cards = document.querySelectorAll(".kpi-card");
  const card = cards[index];

  if (!card) return;

  const value = card.querySelector(".kpi-value");
  const note = card.querySelector(".kpi-note");

  if (value) value.textContent = data.value;
  if (note) note.textContent = data.note;
}

function setLiveStatus(text) {
  const indicator = document.querySelector(".live-indicator");

  if (!indicator) return;

  indicator.textContent = text;
}

function getTodayClasses(classes) {
  const today = new Date();
  const days = [
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
  ];

  const todayName = days[today.getDay()];

  return classes.filter((gymClass) => gymClass.day_of_week === todayName);
}

function isToday(dateValue) {
  if (!dateValue) return false;

  const date = new Date(dateValue);
  const today = new Date();

  return date.toDateString() === today.toDateString();
}

function isCurrentMonth(dateValue) {
  if (!dateValue) return false;

  const date = new Date(dateValue);
  const today = new Date();

  return (
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
  );
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}