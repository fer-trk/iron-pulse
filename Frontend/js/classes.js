document.addEventListener("DOMContentLoaded", loadClasses);

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

async function loadClasses() {
    showLoading("classes-table-container");
    try {
        const classes = await getData("/shifts/");
        renderClassesTable(classes);
    } catch (error) {
        console.error("Error loading classes:", error);
        showError("classes-table-container", "Could not load classes. Check server connection.");
    }
}

function renderClassesTable(classes) {
    const container = document.getElementById("classes-table-container");

    if (!classes || classes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h5>No classes found</h5>
                <p>Create the first class to start managing the gym schedule.</p>
            </div>`;
        return;
    }

    container.innerHTML = `
        <div class="table-responsive">
            <table class="table align-middle">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Class</th>
                        <th>Instructor</th>
                        <th>Day</th>
                        <th>Time</th>
                        <th>Capacity</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${classes.map(item => `
                        <tr>
                            <td>${item.id}</td>
                            <td class="fw-semibold">${item.class_name}</td>
                            <td>${item.instructor || "-"}</td>
                            <td class="text-capitalize">${item.day_of_week}</td>
                            <td>${item.start_time} - ${item.end_time}</td>
                            <td>${item.max_capacity}</td>
                            <td>${item.active_slot
                                ? '<span class="badge badge-soft-success">Active</span>'
                                : '<span class="badge badge-soft-danger">Inactive</span>'
                            }</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary me-1"
                                    onclick="openEditModal(${item.id}, '${item.class_name.replace(/'/g,"\\'")}', '${item.instructor.replace(/'/g,"\\'")}', '${item.day_of_week}', '${item.start_time}', '${item.end_time}', ${item.max_capacity}, ${item.active_slot})">
                                    <i class="bi bi-pencil"></i> Edit
                                </button>
                                <button class="btn btn-sm btn-outline-danger"
                                    onclick="confirmDeleteClass(${item.id}, '${item.class_name.replace(/'/g,"\\'")}')">
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
    document.getElementById("form-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("addClassModal")).show();
}

async function submitAddClass() {
    const name     = document.getElementById("className").value.trim();
    const instructor = document.getElementById("classInstructor").value.trim();
    const dayOfWeek  = document.getElementById("classDayOfWeek").value;
    const start    = document.getElementById("classStart").value;
    const end      = document.getElementById("classEnd").value;
    const capacity = document.getElementById("classCapacity").value;
    const errorDiv = document.getElementById("form-error");

    if (!name || !instructor || !start || !end || !capacity) {
        errorDiv.textContent = "Please fill in all required fields.";
        errorDiv.classList.remove("d-none");
        return;
    }

    errorDiv.classList.add("d-none");

    try {
        await postData("/shifts/", {
            class_name:   name,
            instructor:   instructor,
            day_of_week:  dayOfWeek,
            start_time:   start,
            end_time:     end,
            max_capacity: parseInt(capacity),
            active_slot:  true
        });
        bootstrap.Modal.getInstance(document.getElementById("addClassModal")).hide();
        showSuccess("Class added successfully!");
        loadClasses();
    } catch (error) {
        errorDiv.textContent = error.message || "Could not save class. Try again.";
        errorDiv.classList.remove("d-none");
    }
}

// ── EDIT ──────────────────────────────────────────────────────────────────
function openEditModal(id, name, instructor, dayOfWeek, start, end, capacity, activeSlot) {
    document.getElementById("editClassId").value         = id;
    document.getElementById("editClassName").value       = name;
    document.getElementById("editClassInstructor").value = instructor;
    document.getElementById("editClassDayOfWeek").value  = dayOfWeek;
    document.getElementById("editClassStart").value      = start;
    document.getElementById("editClassEnd").value        = end;
    document.getElementById("editClassCapacity").value   = capacity;
    document.getElementById("editClassStatus").value     = activeSlot ? "true" : "false";
    document.getElementById("edit-class-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("editClassModal")).show();
}

async function submitEditClass() {
    const id         = document.getElementById("editClassId").value;
    const name       = document.getElementById("editClassName").value.trim();
    const instructor = document.getElementById("editClassInstructor").value.trim();
    const dayOfWeek  = document.getElementById("editClassDayOfWeek").value;
    const start      = document.getElementById("editClassStart").value;
    const end        = document.getElementById("editClassEnd").value;
    const capacity   = document.getElementById("editClassCapacity").value;
    const activeSlot = document.getElementById("editClassStatus").value === "true";
    const errorDiv   = document.getElementById("edit-class-error");

    if (!name || !instructor || !start || !end || !capacity) {
        errorDiv.textContent = "Please fill in all required fields.";
        errorDiv.classList.remove("d-none");
        return;
    }

    errorDiv.classList.add("d-none");

    try {
        await patchData(`/shifts/${id}`, {
            class_name:   name,
            instructor:   instructor,
            day_of_week:  dayOfWeek,
            start_time:   start,
            end_time:     end,
            max_capacity: parseInt(capacity),
            active_slot:  activeSlot
        });
        bootstrap.Modal.getInstance(document.getElementById("editClassModal")).hide();
        showSuccess("Class updated successfully!");
        loadClasses();
    } catch (error) {
        errorDiv.textContent = error.message || "Could not update class. Try again.";
        errorDiv.classList.remove("d-none");
    }
}

// ── DELETE ────────────────────────────────────────────────────────────────
function confirmDeleteClass(id, name) {
    document.getElementById("deleteClassId").value = id;
    document.getElementById("deleteClassName").textContent = name;
    document.getElementById("delete-class-error").classList.add("d-none");
    new bootstrap.Modal(document.getElementById("deleteClassModal")).show();
}

async function submitDeleteClass() {
    const id       = document.getElementById("deleteClassId").value;
    const errorDiv = document.getElementById("delete-class-error");
    errorDiv.classList.add("d-none");

    try {
        await deleteData(`/shifts/${id}`);
        bootstrap.Modal.getInstance(document.getElementById("deleteClassModal")).hide();
        showSuccess("Class deleted successfully.");
        loadClasses();
    } catch (error) {
        errorDiv.textContent = error.message || "Could not delete class. Try again.";
        errorDiv.classList.remove("d-none");
    }
}