requireAuth();

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const SLOTS = ["09:00", "10:00", "11:15", "12:15", "14:00", "15:00", "16:00"];

let coursesCache = {};
let teachersCache = {};
let roomsCache = {};

async function loadLookups() {
    const [courses, teachers, rooms] = await Promise.all([
        apiCall("/api/courses/").catch(() => []),
        apiCall("/api/teachers/").catch(() => []),
        apiCall("/api/rooms/").catch(() => [])
    ]);
    courses.forEach(c => coursesCache[c.id] = c);
    teachers.forEach(t => teachersCache[t.id] = t);
    rooms.forEach(r => roomsCache[r.id] = r);
}

async function loadTimetable() {
    const tbody = document.getElementById("timetableBody");
    try {
        const entries = await apiCall("/api/timetable/");

        if (!entries.length) {
            tbody.innerHTML = `<tr><td colspan="6" class="no-data">
                No timetable yet. Click "Auto-Generate" to create one.
            </td></tr>`;
            return;
        }

        tbody.innerHTML = SLOTS.map(slot => {
            const cells = DAYS.map(day => {
                const cellEntries = entries.filter(e =>
                    e.day === day && e.start_time === slot
                );

                if (!cellEntries.length) return `<td></td>`;

                const content = cellEntries.map(e => {
                    const course = coursesCache[e.course_id] || {};
                    const teacher = teachersCache[e.teacher_id] || {};
                    const room = roomsCache[e.room_id] || {};
                    const isLocked = e.is_locked === 1;
                    return `
                        <div class="slot-entry ${isLocked ? 'locked' : ''}">
                            <div class="slot-entry-content">
                                <span class="course-name">${course.code || "?"} — ${course.name || "?"}</span>
                                <span class="teacher-name">👤 ${teacher.name || "?"}</span>
                                <span class="room-name">🏫 ${room.name || "?"}</span>
                            </div>
                            <button class="lock-btn"
                                    onclick="toggleLock(${e.id}, ${e.is_locked || 0})"
                                    title="${isLocked ? 'Unlock' : 'Lock this slot'}">
                                ${isLocked ? '🔒' : '🔓'}
                            </button>
                        </div>
                    `;
                }).join("");

                return `<td>${content}</td>`;
            }).join("");

            return `
                <tr>
                    <td class="time-col">${slot}</td>
                    ${cells}
                </tr>
            `;
        }).join("");

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="no-data" style="color:#dc2626;">
            Error: ${err.message}
        </td></tr>`;
    }
}

async function autoGenerate() {
    const btn = document.getElementById("genBtn");
    const msgDiv = document.getElementById("genMessage");

    if (!confirm("This will clear unlocked entries and generate a new timetable. Continue?")) return;

    btn.disabled = true;
    btn.textContent = "Generating...";
    msgDiv.innerHTML = "";

    try {
        const result = await apiCall("/api/timetable/auto-generate", "POST");

        let message = `✅ ${result.message} — Placed ${result.placed}/${result.total_courses} courses.`;
        if (result.locked_preserved > 0) {
            message += ` 🔒 ${result.locked_preserved} locked slots preserved.`;
        }

        if (result.unplaced_count > 0) {
            msgDiv.innerHTML = `<div class="error-banner">⚠️ Could not place: ${result.unplaced.join(", ")}</div>`;
        } else {
            msgDiv.innerHTML = `<div class="success-msg">${message}</div>`;
        }

        await loadLookups();
        await loadTimetable();
    } catch (err) {
        msgDiv.innerHTML = `<div class="error-banner">❌ ${err.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = "⚡ Auto-Generate";
    }
}

async function toggleLock(entryId, currentState) {
    const newState = currentState === 1 ? 0 : 1;
    try {
        await apiCall(`/api/timetable/${entryId}/lock`, "PUT", { is_locked: newState });
        await loadTimetable();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

(async () => {
    await loadLookups();
    await loadTimetable();
})();
