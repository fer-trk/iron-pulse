document.addEventListener("DOMContentLoaded", async () => {
  try {
    const now = new Date(), first = new Date(now.getFullYear(), now.getMonth(), 1);
    const day = d => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
    const [members, plans, income, enrollments] = await Promise.all([getAllData("/members/?is_active=true"), getData("/plans/?active=true"), getData(`/reports/income?start_date=${day(first)}&end_date=${day(now)}`), getAllData("/reservations/")]);
    document.getElementById("dashboard-members").textContent = members.length;
    document.getElementById("dashboard-plans").textContent = plans.length;
    document.getElementById("dashboard-income").textContent = formatCurrency(income.total_income);
    document.getElementById("dashboard-enrollments").textContent = enrollments.filter(x => x.status === "confirmed" && x.date >= day(now)).length;
  } catch (error) { document.getElementById("dashboard-message").textContent = error.message; }
});
