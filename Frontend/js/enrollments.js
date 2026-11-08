document.addEventListener("DOMContentLoaded", async () => {
  document.getElementById("enrollment-form").addEventListener("submit", submitEnrollment);
  document.getElementById("enrollment-shift").addEventListener("change", suggestClassDate);
  await loadEnrollments();
});
let enrollmentMembers = [], enrollmentShifts = [];
function localDay(date = new Date()) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}
function suggestClassDate() {
  const shift = enrollmentShifts.find(s => s.id === Number(document.getElementById("enrollment-shift").value));
  if (!shift) return;
  const days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
  const next = new Date();
  next.setDate(next.getDate() + (days.indexOf(shift.day_of_week) - next.getDay() + 7) % 7);
  document.getElementById("enrollment-date").value = localDay(next);
}
async function loadEnrollments() {
  try {
    const [members, shifts, records] = await Promise.all([getAllData("/members/"), getData("/shifts/"), getAllData("/reservations/")]);
    enrollmentMembers = members; enrollmentShifts = shifts;
    const m = document.getElementById("enrollment-member"), s = document.getElementById("enrollment-shift");
    m.replaceChildren(new Option("Select a member", ""));
    members.filter(x => x.is_active).forEach(x => m.add(new Option(`${x.first_name} ${x.last_name}`, x.id)));
    s.replaceChildren(new Option("Select a class", ""));
    shifts.filter(x => x.active_slot).forEach(x => s.add(new Option(`${x.class_name} · ${x.day_of_week} ${x.start_time}`, x.id)));
    document.getElementById("enrollment-date").min = localDay();
    const body = document.getElementById("enrollment-rows"); body.replaceChildren();
    records.forEach(record => {
      const row = document.createElement("tr");
      const member = members.find(x => x.id === record.member_id), shift = shifts.find(x => x.id === record.shift_id);
      const values = [member ? `${member.first_name} ${member.last_name}` : `Member ${record.member_id}`, shift?.class_name || `Class ${record.shift_id}`, record.date, record.status];
      values.forEach(value => { const cell = document.createElement("td"); cell.textContent = value; row.append(cell); });
      const action = document.createElement("td");
      if (record.status === "confirmed") {
        const button = document.createElement("button"); button.textContent = "Cancel enrollment"; button.className = "btn btn-sm btn-outline-danger";
        button.addEventListener("click", async () => {
          try { await patchData(`/reservations/${record.id}/cancel`, {}); await loadEnrollments(); }
          catch (error) { document.getElementById("enrollment-message").textContent = error.message; }
        }); action.append(button);
      }
      row.append(action); body.append(row);
    });
  } catch (error) { document.getElementById("enrollment-message").textContent = error.message; }
}
async function submitEnrollment(event) {
  event.preventDefault();
  try {
    await postData("/reservations/", { member_id: Number(document.getElementById("enrollment-member").value), shift_id: Number(document.getElementById("enrollment-shift").value), date: document.getElementById("enrollment-date").value });
    document.getElementById("enrollment-message").textContent = "Member enrolled successfully.";
    await loadEnrollments();
  } catch (error) { document.getElementById("enrollment-message").textContent = error.message; }
}
