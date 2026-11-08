document.addEventListener("DOMContentLoaded", () => {
  const now = new Date(), first = new Date(now.getFullYear(), now.getMonth(), 1);
  const day = d => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  document.getElementById("income-start").value = day(first);
  document.getElementById("income-end").value = day(now);
  document.getElementById("income-form").addEventListener("submit", event => { event.preventDefault(); loadIncome(); });
  loadIncome();
});
async function loadIncome() {
  try {
    const start = document.getElementById("income-start").value, end = document.getElementById("income-end").value;
    const report = await getData(`/reports/income?start_date=${encodeURIComponent(start)}&end_date=${encodeURIComponent(end)}`);
    document.getElementById("income-total").textContent = formatCurrency(report.total_income);
    document.getElementById("income-count").textContent = report.total_payments;
    document.getElementById("income-message").textContent = "";
  } catch (error) { document.getElementById("income-message").textContent = error.message; }
}
