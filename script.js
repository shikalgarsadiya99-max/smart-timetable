/* Smart Timetable — consolidated JavaScript from api.js, auth.js, dashboard.js,
   teachers.js, courses.js, rooms.js and timetable.js. */
const API_URL = "http://localhost:8000";

function getToken() { return localStorage.getItem("token"); }
function setToken(token) { localStorage.setItem("token", token); }
function getUser() {
  try { return JSON.parse(localStorage.getItem("user") || "null"); }
  catch { return null; }
}
function setUser(user) { localStorage.setItem("user", JSON.stringify(user)); }
function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  showAuth();
}
async function apiCall(endpoint, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const options = { method, headers };
  if (body !== null && body !== undefined) options.body = JSON.stringify(body);
  let response;
  try {
    response = await fetch(`${API_URL}${endpoint}`, options);
  } catch (error) {
    throw new Error(`Cannot connect to backend at ${API_URL}. Make sure the backend is running and CORS allows this frontend.`);
  }
  if (response.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    showAuth();
    throw new Error("Session expired. Please log in again.");
  }
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || err.message || `Request failed (${response.status})`);
  }
  if (response.status === 204) return null;
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}
function requireAuth() {
  if (!getToken()) { showAuth(); return false; }
  return true;
}
function isAdmin() {
  const user = getUser();
  return !!(user && user.role === "admin");
}
function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) el.textContent = message;
}
function formatName(name) { return name ? name.charAt(0).toUpperCase() + name.slice(1) : ""; }

const views = ["dashboard", "teachers", "courses", "rooms", "timetable"];
let currentView = "dashboard";

function showAuth() {
  document.getElementById("authView").classList.remove("hidden");
  document.getElementById("appView").classList.add("hidden");
}
function showApp() {
  document.getElementById("authView").classList.add("hidden");
  document.getElementById("appView").classList.remove("hidden");
  const user = getUser();
  if (user) {
    document.getElementById("userName").textContent = user.username || "User";
    document.getElementById("userRole").textContent = user.role || "user";
  }
  navigate("dashboard");
  loadStats();
}
function navigate(view) {
  if (!views.includes(view)) view = "dashboard";
  if (!getToken()) { showAuth(); return; }
  currentView = view;
  document.querySelectorAll(".page-view").forEach(el => el.classList.add("hidden"));
  const target = document.getElementById(`${view}View`);
  if (target) target.classList.remove("hidden");
  document.querySelectorAll(".sidebar nav a[data-view]").forEach(a => a.classList.toggle("active", a.dataset.view === view));
  if (view === "dashboard") loadStats();
  if (view === "teachers") loadTeachers();
  if (view === "courses") initCourses();
  if (view === "rooms") loadRooms();
  if (view === "timetable") initTimetable();
}
document.querySelectorAll(".sidebar nav a[data-view]").forEach(a => a.addEventListener("click", e => {
  e.preventDefault();
  navigate(a.dataset.view);
}));
document.querySelectorAll("[data-go]").forEach(el => el.addEventListener("click", () => navigate(el.dataset.go)));
document.getElementById("logoutLink").addEventListener("click", e => { e.preventDefault(); logout(); });

function switchTab(tab) {
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const loginTab = document.getElementById("loginTab");
  const registerTab = document.getElementById("registerTab");
  if (tab === "login") {
    loginForm.classList.remove("hidden"); registerForm.classList.add("hidden");
    loginTab.classList.add("active"); registerTab.classList.remove("active");
  } else {
    loginForm.classList.add("hidden"); registerForm.classList.remove("hidden");
    loginTab.classList.remove("active"); registerTab.classList.add("active");
  }
}
document.getElementById("loginForm").addEventListener("submit", async e => {
  e.preventDefault(); showError("loginError", "");
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;
  try {
    const data = await apiCall("/api/users/login", "POST", { username, password });
    setToken(data.access_token);
    setUser({ username: data.username, role: data.role });
    showApp();
  } catch (err) { showError("loginError", err.message); }
});
document.getElementById("registerForm").addEventListener("submit", async e => {
  e.preventDefault(); showError("registerError", "");
  const email = document.getElementById("regEmail").value.trim();
  const username = document.getElementById("regUsername").value.trim();
  const password = document.getElementById("regPassword").value;
  const role = document.getElementById("regRole").value;
  try {
    await apiCall("/api/users/register", "POST", { email, username, password, role });
    alert("Registration successful! Please log in.");
    switchTab("login");
  } catch (err) { showError("registerError", err.message); }
});

// Dashboard
async function loadStats() {
  if (!getToken()) return;
  const ids = ["teacherCount", "courseCount", "roomCount", "timetableCount"];
  try {
    const [teachers, courses, rooms, timetable] = await Promise.all([
      apiCall("/api/teachers/").catch(() => []),
      apiCall("/api/courses/").catch(() => []),
      apiCall("/api/rooms/").catch(() => []),
      apiCall("/api/timetable/").catch(() => [])
    ]);
    document.getElementById(ids[0]).textContent = Array.isArray(teachers) ? teachers.length : "—";
    document.getElementById(ids[1]).textContent = Array.isArray(courses) ? courses.length : "—";
    document.getElementById(ids[2]).textContent = Array.isArray(rooms) ? rooms.length : "—";
    document.getElementById(ids[3]).textContent = Array.isArray(timetable) ? timetable.length : "—";
  } catch (err) { console.error("Failed to load stats:", err); }
}

// Teachers
function toggleOrgField() {
  const type = document.getElementById("tType").value;
  document.getElementById("orgGroup").classList.toggle("hidden", type !== "external");
}
async function loadTeachers() {
  const tbody = document.getElementById("teachersBody");
  try {
    const teachers = await apiCall("/api/teachers/");
    if (!Array.isArray(teachers) || !teachers.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="no-data">No teachers yet. Add one above!</td></tr>'; return;
    }
    tbody.innerHTML = teachers.map(t => `<tr>
      <td>${escapeHTML(t.id)}</td><td>${escapeHTML(t.name)}</td><td>${escapeHTML(t.email)}</td>
      <td>${escapeHTML(t.department)}</td><td><span class="badge badge-${t.type === "external" ? "external" : "internal"}">${escapeHTML(t.type)}</span></td>
      <td>${escapeHTML(t.max_workload)}</td><td><button class="btn btn-danger" onclick="deleteTeacher(${Number(t.id)})">Delete</button></td>
    </tr>`).join("");
  } catch (err) { tbody.innerHTML = `<tr><td colspan="7" class="no-data" style="color:#dc2626">Error: ${escapeHTML(err.message)}</td></tr>`; }
}
async function deleteTeacher(id) {
  if (!confirm("Delete this teacher?")) return;
  try { await apiCall(`/api/teachers/${id}`, "DELETE"); await loadTeachers(); }
  catch (err) { alert("Error: " + err.message); }
}
document.getElementById("teacherForm").addEventListener("submit", async e => {
  e.preventDefault(); showError("teacherError", "");
  const body = {
    name: document.getElementById("tName").value.trim(),
    email: document.getElementById("tEmail").value.trim(),
    department: document.getElementById("tDept").value.trim(),
    type: document.getElementById("tType").value,
    max_workload: parseInt(document.getElementById("tWorkload").value, 10),
    organization: document.getElementById("tOrg").value.trim()
  };
  try {
    await apiCall("/api/teachers/", "POST", body);
    e.target.reset(); document.getElementById("tWorkload").value = 18; toggleOrgField(); await loadTeachers();
  } catch (err) { showError("teacherError", err.message); }
});

// Courses
let teachersCache = [];
async function loadTeachersDropdown() {
  teachersCache = await apiCall("/api/teachers/");
  if (!Array.isArray(teachersCache)) teachersCache = [];
  const select = document.getElementById("cTeacher");
  select.innerHTML = teachersCache.map(t => `<option value="${Number(t.id)}">${escapeHTML(t.name)} (${escapeHTML(t.department)})</option>`).join("");
  if (!teachersCache.length) select.innerHTML = '<option value="">Add a teacher first</option>';
}
async function loadCourses() {
  const tbody = document.getElementById("coursesBody");
  try {
    const courses = await apiCall("/api/courses/");
    if (!Array.isArray(courses) || !courses.length) { tbody.innerHTML = '<tr><td colspan="8" class="no-data">No courses yet.</td></tr>'; return; }
    tbody.innerHTML = courses.map(c => {
      const teacher = teachersCache.find(t => String(t.id) === String(c.teacher_id));
      return `<tr><td>${escapeHTML(c.id)}</td><td>${escapeHTML(c.code)}</td><td>${escapeHTML(c.name)}</td>
        <td>${escapeHTML(c.credits)}</td><td>${escapeHTML(teacher ? teacher.name : "—")}</td>
        <td>${escapeHTML(c.class_name)}</td><td>${escapeHTML(c.department)}</td>
        <td><button class="btn btn-danger" onclick="deleteCourse(${Number(c.id)})">Delete</button></td></tr>`;
    }).join("");
  } catch (err) { tbody.innerHTML = `<tr><td colspan="8" class="no-data" style="color:#dc2626">Error: ${escapeHTML(err.message)}</td></tr>`; }
}
async function deleteCourse(id) {
  if (!confirm("Delete this course?")) return;
  try { await apiCall(`/api/courses/${id}`, "DELETE"); await loadCourses(); }
  catch (err) { alert("Error: " + err.message); }
}
document.getElementById("courseForm").addEventListener("submit", async e => {
  e.preventDefault(); showError("courseError", "");
  const body = {
    name: document.getElementById("cName").value.trim(),
    code: document.getElementById("cCode").value.trim(),
    credits: parseInt(document.getElementById("cCredits").value, 10),
    teacher_id: parseInt(document.getElementById("cTeacher").value, 10),
    semester: parseInt(document.getElementById("cSemester").value, 10),
    department: document.getElementById("cDept").value.trim(),
    class_name: document.getElementById("cClass").value.trim()
  };
  try { await apiCall("/api/courses/", "POST", body); e.target.reset(); document.getElementById("cCredits").value = 3; document.getElementById("cSemester").value = 1; await initCourses(); }
  catch (err) { showError("courseError", err.message); }
});
async function initCourses() {
  try { await loadTeachersDropdown(); await loadCourses(); }
  catch (err) { document.getElementById("coursesBody").innerHTML = `<tr><td colspan="8" class="no-data" style="color:#dc2626">Error: ${escapeHTML(err.message)}</td></tr>`; }
}

// Rooms
async function loadRooms() {
  const grid = document.getElementById("roomsGrid");
  try {
    const rooms = await apiCall("/api/rooms/");
    if (!Array.isArray(rooms) || !rooms.length) { grid.innerHTML = '<p class="no-data">No rooms yet. Add one above!</p>'; return; }
    grid.innerHTML = rooms.map(r => `<div class="room-card"><div><h3>${escapeHTML(r.name)}</h3><p>Capacity: ${escapeHTML(r.capacity)}</p><span class="badge badge-${r.type === "lab" ? "lab" : "classroom"}">${escapeHTML(r.type)}</span></div><button class="btn btn-danger" style="margin-top:12px" onclick="deleteRoom(${Number(r.id)})">Delete</button></div>`).join("");
  } catch (err) { grid.innerHTML = `<p class="no-data" style="color:#dc2626">Error: ${escapeHTML(err.message)}</p>`; }
}
async function deleteRoom(id) {
  if (!confirm("Delete this room?")) return;
  try { await apiCall(`/api/rooms/${id}`, "DELETE"); await loadRooms(); }
  catch (err) { alert("Error: " + err.message); }
}
document.getElementById("roomForm").addEventListener("submit", async e => {
  e.preventDefault(); showError("roomError", "");
  const body = { name: document.getElementById("rName").value.trim(), capacity: parseInt(document.getElementById("rCapacity").value, 10), type: document.getElementById("rType").value };
  try { await apiCall("/api/rooms/", "POST", body); e.target.reset(); document.getElementById("rCapacity").value = 60; await loadRooms(); }
  catch (err) { showError("roomError", err.message); }
});

// Timetable
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const SLOTS = ["09:00", "10:00", "11:15", "12:15", "14:00", "15:00", "16:00"];
let coursesCacheById = {}, teachersCacheById = {}, roomsCacheById = {};
async function loadLookups() {
  const [courses, teachers, rooms] = await Promise.all([
    apiCall("/api/courses/").catch(() => []), apiCall("/api/teachers/").catch(() => []), apiCall("/api/rooms/").catch(() => [])
  ]);
  coursesCacheById = {}; teachersCacheById = {}; roomsCacheById = {};
  (courses || []).forEach(c => coursesCacheById[c.id] = c);
  (teachers || []).forEach(t => teachersCacheById[t.id] = t);
  (rooms || []).forEach(r => roomsCacheById[r.id] = r);
}
async function loadTimetable() {
  const tbody = document.getElementById("timetableBody");
  try {
    const entries = await apiCall("/api/timetable/");
    if (!Array.isArray(entries) || !entries.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="no-data">No timetable yet. Click "Auto-Generate" to create one.</td></tr>'; return;
    }
    tbody.innerHTML = SLOTS.map(slot => {
      const cells = DAYS.map(day => {
        const cellEntries = entries.filter(e => e.day === day && e.start_time === slot);
        if (!cellEntries.length) return "<td></td>";
        const content = cellEntries.map(e => {
          const course = coursesCacheById[e.course_id] || {}, teacher = teachersCacheById[e.teacher_id] || {}, room = roomsCacheById[e.room_id] || {};
          return `<div class="slot-entry"><span class="course-name">${escapeHTML(course.code || "?")} — ${escapeHTML(course.name || "?")}</span><span class="teacher-name">👤 ${escapeHTML(teacher.name || "?")}</span><span class="room-name">🏫 ${escapeHTML(room.name || "?")}</span></div>`;
        }).join("");
        return `<td>${content}</td>`;
      }).join("");
      return `<tr><td class="time-col">${slot}</td>${cells}</tr>`;
    }).join("");
  } catch (err) { tbody.innerHTML = `<tr><td colspan="6" class="no-data" style="color:#dc2626">Error: ${escapeHTML(err.message)}</td></tr>`; }
}
async function autoGenerate() {
  const btn = document.getElementById("genBtn"), msg = document.getElementById("genMessage");
  if (!confirm("This will clear the existing timetable and generate a new one. Continue?")) return;
  btn.disabled = true; btn.textContent = "Generating..."; msg.textContent = "";
  try {
    const result = await apiCall("/api/timetable/auto-generate", "POST");
    msg.style.color = "#16a34a";
    msg.textContent = `✅ ${result.message} — Placed ${result.placed}/${result.total_courses} courses.`;
    if (result.unplaced_count > 0) { msg.style.color = "#dc2626"; msg.textContent += ` ⚠️ Could not place: ${(result.unplaced || []).join(", ")}`; }
    await loadLookups(); await loadTimetable();
  } catch (err) { msg.style.color = "#dc2626"; msg.textContent = "❌ " + err.message; }
  finally { btn.disabled = false; btn.textContent = "⚡ Auto-Generate Timetable"; }
}
async function initTimetable() { await loadLookups(); await loadTimetable(); }

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[ch]));
}

// Initial state: preserve login if a token exists, otherwise show authentication.
if (getToken()) showApp(); else showAuth();