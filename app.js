const API="http://localhost:8000";
const DAYS=["Tuesday","Wednesday","Thursday","Friday","Saturday"];
const SLOTS=["09:00","10:00","11:15","12:15","14:00","15:00","16:00"];

/* ============ HELPERS ============ */
const $=id=>document.getElementById(id);
const getToken=()=>localStorage.getItem("token");
const setToken=t=>localStorage.setItem("token",t);
const getUser=()=>JSON.parse(localStorage.getItem("user")||"null");
const setUser=u=>localStorage.setItem("user",JSON.stringify(u));
function logout(){localStorage.clear();location.reload()}

async function api(path,method="GET",body=null){
  const h={"Content-Type":"application/json"};
  const t=getToken();
  if(t)h.Authorization=`Bearer ${t}`;
  const o={method,headers:h};
  if(body)o.body=JSON.stringify(body);
  const r=await fetch(API+path,o);
  if(r.status===401){logout();throw new Error("Session expired")}
  if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(e.detail||`Error ${r.status}`)}
  return r.status===204?null:r.json();
}

/* ============ AUTH ============ */
function switchAuthTab(t){
  $("loginForm").classList.toggle("hidden",t!=="login");
  $("registerForm").classList.toggle("hidden",t!=="register");
  $("loginTab").classList.toggle("active",t==="login");
  $("registerTab").classList.toggle("active",t==="register");
}

function toggleRoleFields(){
  const r=$("regRole").value;
  $("studentFields").classList.toggle("hidden",r!=="student");
  $("intPasswordHint").textContent=r==="admin"?"Choose a unique number":r==="teacher"?"Enter admin password":"Enter your college admin password";
}

async function loadRegDepartments(){
  try{
    const depts=await api("/api/departments/");
    const sel=$("regDept");
    if(!sel)return;
    sel.innerHTML='<option value="">Select Department</option>'+
      depts.map(d=>`<option value="${d.code}">${d.name}</option>`).join("");
  }catch(e){}
}

async function loadDivisionsForReg(){
  const d=$("regDept").value,s=$("regSemester").value,sel=$("regDivision");
  $("regBatch").innerHTML='<option value="">Select</option>';
  if(!d||!s){sel.innerHTML='<option value="">Select</option>';return}
  try{
    const divs=await api("/api/divisions/");
    const f=divs.filter(x=>x.department===d&&x.semester===parseInt(s));
    sel.innerHTML='<option value="">Select</option>'+f.map(x=>`<option value="${x.name}">${x.name}</option>`).join("");
  }catch(e){sel.innerHTML='<option value="">Error</option>'}
}

async function loadBatchesForReg(){
  const dn=$("regDivision").value,sel=$("regBatch");
  if(!dn){sel.innerHTML='<option value="">Select</option>';return}
  try{
    const divs=await api("/api/divisions/");
    const d=divs.find(x=>x.name===dn);if(!d)return;
    const bs=await api(`/api/batches/by-division/${d.id}`);
    sel.innerHTML='<option value="">Select</option>'+bs.map(b=>`<option value="${b.name}">${b.name}</option>`).join("");
  }catch(e){}
}

$("loginForm").addEventListener("submit",async e=>{
  e.preventDefault();$("loginError").textContent="";
  try{
    const d=await api("/api/users/login","POST",{
      username:$("loginUsername").value.trim(),
      password:$("loginPassword").value,
      int_password:parseInt($("loginIntPassword").value)
    });
    setToken(d.access_token);setUser(d.user);location.reload();
  }catch(err){$("loginError").textContent=err.message}
});

$("registerForm").addEventListener("submit",async e=>{
  e.preventDefault();$("registerError").textContent="";
  const role=$("regRole").value;
  const body={
    email:$("regEmail").value.trim(),
    username:$("regUsername").value.trim(),
    password:$("regPassword").value,
    role,
    int_password:parseInt($("regIntPassword").value)
  };
  if(role==="student"){
    body.department=$("regDept").value;
    body.semester=parseInt($("regSemester").value);
    body.division=$("regDivision").value;
    body.batch=$("regBatch").value;

    if(!body.department || !body.semester) {
      return $("registerError").textContent = "Select Department and Semester";
    }
    if ($("regDivision").options.length <= 1) {
      return $("registerError").textContent = "No divisions for this Department+Semester. Contact admin.";
    }
    if(!body.division) {
      return $("registerError").textContent = "Please select a Division";
    }
    if ($("regBatch").options.length <= 1) {
      return $("registerError").textContent = "No batches for this division. Contact admin.";
    }
    if(!body.batch) {
      return $("registerError").textContent = "Please select a Batch";
    }
  }
  try{
    await api("/api/users/register","POST",body);
    alert("Registration successful! Please log in.");
    switchAuthTab("login");e.target.reset();
  }catch(err){$("registerError").textContent=err.message}
});

/* ============ ROUTER ============ */
const ROUTES={};
let currentRoute="dashboard";

function navigate(route){
  currentRoute=route;
  document.querySelectorAll(".sidebar nav a").forEach(a=>{
    a.classList.toggle("active",a.dataset.route===route)
  });
  ROUTES[route]?.();
}

function buildNav(){
  const u=getUser();if(!u)return;
  const links=u.role==="admin"?[
    ["dashboard","🏠 Dashboard"],
    ["departments","🏢 Departments"],
    ["divisions","🏛️ Divisions"],
    ["batches","👥 Batches"],
    ["teachers","👨‍🏫 Teachers"],
    ["courses","📚 Courses"],
    ["rooms","🏫 Rooms"],
    ["constraints","⚙️ Constraints"],
    ["timetable","🗓️ Timetable"],
    ["profile","👤 Profile"]
  ]:u.role==="teacher"?[
    ["teacherSchedule","🗓️ My Schedule"],["profile","👤 Profile"]
  ]:[
    ["studentTimetable","🗓️ My Timetable"],["profile","👤 Profile"]
  ];
  $("sidebarNav").innerHTML=links.map(([r,l])=>`<a href="#" data-route="${r}" onclick="event.preventDefault();navigate('${r}')">${l}</a>`).join("")
    +`<a href="#" class="logout" onclick="event.preventDefault();logout()">🚪 Logout</a>`;
  $("userInfo").innerHTML=`<strong>${u.username}</strong> (${u.role})`;
}

/* ============ DEPARTMENTS ============ */
ROUTES.departments=async()=>{
  $("pageTitle").textContent="Manage Departments";
  $("content").innerHTML=`
    <div class="card"><h2>Add New Department</h2>
      <form id="depForm"><div class="form-row">
        <div class="form-group"><label>Name</label><input id="depName" placeholder="Computer Science" required></div>
        <div class="form-group"><label>Code</label><input id="depCode" placeholder="CS" required></div>
        <div class="form-group"><label>HOD</label><input id="depHod" placeholder="Dr. Patil"></div>
      </div><button class="btn btn-primary" style="width:auto;margin-top:12px">Add Department</button>
      <p class="error-msg" id="depErr"></p></form></div>
    <div class="card"><h2>All Departments</h2><div id="depList"></div></div>`;
  $("depForm").onsubmit=async e=>{
    e.preventDefault();
    try{
      await api("/api/departments/","POST",{
        name:$("depName").value,
        code:$("depCode").value,
        hod:$("depHod").value||null
      });
      e.target.reset();loadDep();
    }catch(err){$("depErr").textContent=err.message}
  };
  loadDep();
};

async function loadDep(){
  try{
    const d=await api("/api/departments/");
    $("depList").innerHTML=d.length?`<table><thead><tr><th>ID</th><th>Name</th><th>Code</th><th>HOD</th><th>Action</th></tr></thead><tbody>
      ${d.map(x=>`<tr><td>${x.id}</td><td><strong>${x.name}</strong></td><td>${x.code}</td><td>${x.hod||"—"}</td>
        <td><button class="btn btn-danger" onclick="delDep(${x.id})">Delete</button></td></tr>`).join("")}
      </tbody></table>`:'<p class="no-data">No departments yet</p>';
  }catch(e){$("depList").innerHTML=`<p class="no-data">${e.message}</p>`}
}

window.delDep=async id=>{
  if(!confirm("Delete this department?"))return;
  await api(`/api/departments/${id}`,"DELETE");
  loadDep();
};

/* ============ DASHBOARD ============ */
ROUTES.dashboard=async()=>{
  $("pageTitle").textContent="Dashboard";
  const c=$("content");
  c.innerHTML=`<div class="stats-grid" id="statsGrid"></div>
    <div class="card"><h2>Quick Actions</h2>
    <p style="color:#6b7280;margin-bottom:14px">Add Departments → Divisions → Batches → Teachers → Courses → Rooms → Generate Timetable.</p>
    <div class="actions">
      <button class="btn btn-primary" style="width:auto" onclick="navigate('departments')">🏢 Manage Departments</button>
      <button class="btn btn-success" style="width:auto" onclick="navigate('timetable')">⚡ Generate Timetable</button>
    </div></div>`;
  try{
    const [t,co,r,tt]=await Promise.all([
      api("/api/teachers/").catch(()=>[]),api("/api/courses/").catch(()=>[]),
      api("/api/rooms/").catch(()=>[]),api("/api/timetable/").catch(()=>[])
    ]);
    $("statsGrid").innerHTML=`
      ${card("Teachers",t.length)}
      ${card("Courses",co.length)}
      ${card("Rooms",r.length)}
      ${card("Timetable Entries",tt.length)}`;
  }catch(e){c.innerHTML+=`<div class="msg-error">${e.message}</div>`}
};
const card=(label,val)=>`<div class="stat-card"><h3>${label}</h3><p class="number">${val}</p></div>`;

/* ============ TEACHERS ============ */
ROUTES.teachers=async()=>{
  $("pageTitle").textContent="Manage Teachers";
  $("content").innerHTML=`
    <div class="card"><h2>Add New Teacher</h2>
      <form id="tForm"><div class="form-row">
        <div class="form-group"><label>Name</label><input id="tName" required></div>
        <div class="form-group"><label>Email</label><input type="email" id="tEmail" required></div>
        <div class="form-group"><label>Department</label><input id="tDept" required></div>
        <div class="form-group"><label>Type</label><select id="tType"><option value="internal">Internal</option><option value="external">External</option></select></div>
        <div class="form-group"><label>Max Workload</label><input type="number" id="tLoad" value="18"></div>
      </div><button class="btn btn-primary" style="width:auto;margin-top:12px">Add Teacher</button>
      <p class="error-msg" id="tErr"></p></form></div>
    <div class="card"><h2>All Teachers</h2><div id="tList"></div></div>`;
  $("tForm").onsubmit=async e=>{
    e.preventDefault();
    try{
      await api("/api/teachers/","POST",{
        name:$("tName").value,email:$("tEmail").value,department:$("tDept").value,
        type:$("tType").value,max_workload:parseInt($("tLoad").value),organization:""
      });
      e.target.reset();loadTeachers();
    }catch(err){$("tErr").textContent=err.message}
  };
  loadTeachers();
};
async function loadTeachers(){
  try{
    const t=await api("/api/teachers/");
    $("tList").innerHTML=t.length?`<table><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Dept</th><th>Type</th><th>Load</th><th>Action</th></tr></thead><tbody>
      ${t.map(x=>`<tr><td>${x.id}</td><td><strong>${x.name}</strong></td><td>${x.email}</td><td>${x.department}</td>
        <td><span class="badge">${x.type}</span></td><td>${x.max_workload}</td>
        <td><button class="btn btn-danger" onclick="delTeacher(${x.id})">Delete</button></td></tr>`).join("")}
      </tbody></table>`:'<p class="no-data">No teachers yet</p>';
  }catch(e){$("tList").innerHTML=`<p class="no-data">${e.message}</p>`}
}
window.delTeacher=async id=>{if(!confirm("Delete?"))return;await api(`/api/teachers/${id}`,"DELETE");loadTeachers()};

/* ============ COURSES ============ */
ROUTES.courses=async()=>{
  $("pageTitle").textContent="Manage Courses";
  const teachers=await api("/api/teachers/").catch(()=>[]);
  $("content").innerHTML=`
    <div class="card"><h2>Add New Course</h2>
      <form id="cForm"><div class="form-row">
        <div class="form-group"><label>Name</label><input id="cName" required></div>
        <div class="form-group"><label>Code</label><input id="cCode" required></div>
        <div class="form-group"><label>Credits</label><input type="number" id="cCredits" value="3" required></div>
        <div class="form-group"><label>Teacher</label><select id="cTeacher">${teachers.map(t=>`<option value="${t.id}">${t.name}</option>`).join("")}</select></div>
        <div class="form-group"><label>Semester</label><input type="number" id="cSem" value="3"></div>
        <div class="form-group"><label>Department</label><input id="cDept" required></div>
        <div class="form-group"><label>Class</label><input id="cClass" placeholder="SY-A" required></div>
        <div class="form-group"><label>Type</label><select id="cType"><option value="theory">Theory</option><option value="lab">Lab</option></select></div>
      </div><button class="btn btn-primary" style="width:auto;margin-top:12px">Add Course</button>
      <p class="error-msg" id="cErr"></p></form></div>
    <div class="card"><h2>All Courses</h2><div id="cList"></div></div>`;
  $("cForm").onsubmit=async e=>{
    e.preventDefault();
    try{
      await api("/api/courses/","POST",{
        name:$("cName").value,code:$("cCode").value,credits:parseInt($("cCredits").value),
        teacher_id:parseInt($("cTeacher").value),semester:parseInt($("cSem").value),
        department:$("cDept").value,class_name:$("cClass").value,course_type:$("cType").value
      });
      e.target.reset();loadCourses();
    }catch(err){$("cErr").textContent=err.message}
  };
  loadCourses();
};
async function loadCourses(){
  try{
    const co=await api("/api/courses/");
    $("cList").innerHTML=co.length?`<table><thead><tr><th>Code</th><th>Name</th><th>Type</th><th>Credits</th><th>Class</th><th>Dept</th><th>Action</th></tr></thead><tbody>
      ${co.map(x=>`<tr><td><strong>${x.code}</strong></td><td>${x.name}</td>
        <td><span class="badge">${x.course_type}</span></td><td>${x.credits}</td>
        <td>${x.class_name}</td><td>${x.department}</td>
        <td><button class="btn btn-danger" onclick="delCourse(${x.id})">Delete</button></td></tr>`).join("")}
      </tbody></table>`:'<p class="no-data">No courses yet</p>';
  }catch(e){$("cList").innerHTML=`<p class="no-data">${e.message}</p>`}
}
window.delCourse=async id=>{if(!confirm("Delete?"))return;await api(`/api/courses/${id}`,"DELETE");loadCourses()};

/* ============ ROOMS ============ */
ROUTES.rooms=async()=>{
  $("pageTitle").textContent="Manage Rooms";
  $("content").innerHTML=`
    <div class="card"><h2>Add New Room</h2>
      <form id="rForm"><div class="form-row">
        <div class="form-group"><label>Name</label><input id="rName" placeholder="A-101" required></div>
        <div class="form-group"><label>Capacity</label><input type="number" id="rCap" value="60" required></div>
        <div class="form-group"><label>Type</label><select id="rType"><option value="classroom">Classroom</option><option value="lab">Lab</option></select></div>
      </div><button class="btn btn-primary" style="width:auto;margin-top:12px">Add Room</button>
      <p class="error-msg" id="rErr"></p></form></div>
    <div class="card"><h2>All Rooms</h2><div id="rList"></div></div>`;
  $("rForm").onsubmit=async e=>{
    e.preventDefault();
    try{
      await api("/api/rooms/","POST",{name:$("rName").value,capacity:parseInt($("rCap").value),type:$("rType").value});
      e.target.reset();loadRooms();
    }catch(err){$("rErr").textContent=err.message}
  };
  loadRooms();
};
async function loadRooms(){
  try{
    const r=await api("/api/rooms/");
    $("rList").innerHTML=r.length?`<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px">
      ${r.map(x=>`<div class="card" style="margin:0;border-left:4px solid #5c6bc0">
        <h3 style="margin-bottom:6px">${x.name}</h3>
        <p style="color:#6b7280;font-size:13px">Capacity: ${x.capacity}</p>
        <span class="badge">${x.type}</span>
        <button class="btn btn-danger" style="margin-top:10px" onclick="delRoom(${x.id})">Delete</button></div>`).join("")}
      </div>`:'<p class="no-data">No rooms yet</p>';
  }catch(e){$("rList").innerHTML=`<p class="no-data">${e.message}</p>`}
}
window.delRoom=async id=>{if(!confirm("Delete?"))return;await api(`/api/rooms/${id}`,"DELETE");loadRooms()};

/* ============ DIVISIONS ============ */
ROUTES.divisions=async()=>{
  $("pageTitle").textContent="Manage Divisions";
  const depts=await api("/api/departments/").catch(()=>[]);
  const deptOptions=depts.length
    ? depts.map(d=>`<option value="${d.code}">${d.name} (${d.code})</option>`).join("")
    : '<option value="">No departments — add one first</option>';
  $("content").innerHTML=`
    <div class="card"><h2>Add New Division</h2>
    ${!depts.length ? '<p style="color:#c62828;font-weight:600">⚠️ Please add a Department first!</p>' : ''}
      <form id="dForm"><div class="form-row">
        <div class="form-group"><label>Name</label><input id="dName" placeholder="SY-A" required></div>
        <div class="form-group"><label>Department</label><select id="dDept">${deptOptions}</select></div>
        <div class="form-group"><label>Semester</label><input type="number" id="dSem" value="3"></div>
        <div class="form-group"><label>Classroom</label><input id="dRoom" placeholder="CSMCR-1"></div>
        <div class="form-group"><label>Students</label><input type="number" id="dStud" value="60"></div>
      </div><button class="btn btn-primary" style="width:auto;margin-top:12px">Add Division</button>
      <p class="error-msg" id="dErr"></p></form></div>
    <div class="card"><h2>All Divisions</h2><div id="dList"></div></div>`;
  $("dForm").onsubmit=async e=>{
    e.preventDefault();
    try{
      await api("/api/divisions/","POST",{
        name:$("dName").value,department:$("dDept").value,semester:parseInt($("dSem").value),
        classroom:$("dRoom").value||null,total_students:parseInt($("dStud").value)
      });
      e.target.reset();loadDivs();
    }catch(err){$("dErr").textContent=err.message}
  };
  loadDivs();
};
async function loadDivs(){
  try{
    const d=await api("/api/divisions/");
    $("dList").innerHTML=d.length?`<table><thead><tr><th>ID</th><th>Name</th><th>Dept</th><th>Sem</th><th>Room</th><th>Students</th><th>Action</th></tr></thead><tbody>
      ${d.map(x=>`<tr><td>${x.id}</td><td><strong>${x.name}</strong></td><td>${x.department}</td>
        <td>${x.semester}</td><td>${x.classroom||"—"}</td><td>${x.total_students}</td>
        <td><button class="btn btn-danger" onclick="delDiv(${x.id})">Delete</button></td></tr>`).join("")}
      </tbody></table>`:'<p class="no-data">No divisions yet</p>';
  }catch(e){$("dList").innerHTML=`<p class="no-data">${e.message}</p>`}
}
window.delDiv=async id=>{if(!confirm("Delete?"))return;await api(`/api/divisions/${id}`,"DELETE");loadDivs()};

/* ============ BATCHES ============ */
ROUTES.batches=async()=>{
  $("pageTitle").textContent="Manage Batches";
  const divs=await api("/api/divisions/").catch(()=>[]);
  $("content").innerHTML=`
    <div class="card"><h2>Add New Batch</h2>
      <form id="bForm"><div class="form-row">
        <div class="form-group"><label>Batch Name</label><input id="bName" placeholder="C12" required></div>
        <div class="form-group"><label>Division</label><select id="bDiv">${divs.map(d=>`<option value="${d.id}">${d.name}</option>`).join("")}</select></div>
      </div><button class="btn btn-primary" style="width:auto;margin-top:12px">Add Batch</button>
      <p class="error-msg" id="bErr"></p></form></div>
    <div class="card"><h2>All Batches</h2><div id="bList"></div></div>`;
  $("bForm").onsubmit=async e=>{
    e.preventDefault();
    try{
      await api("/api/batches/","POST",{name:$("bName").value,division_id:parseInt($("bDiv").value)});
      e.target.reset();loadBats(divs);
    }catch(err){$("bErr").textContent=err.message}
  };
  loadBats(divs);
};
async function loadBats(divs){
  try{
    const b=await api("/api/batches/");
    const dm={};divs?.forEach(d=>dm[d.id]=d.name);
    if(!divs){const d=await api("/api/divisions/");d.forEach(x=>dm[x.id]=x.name)}
    $("bList").innerHTML=b.length?`<table><thead><tr><th>ID</th><th>Name</th><th>Division</th><th>Action</th></tr></thead><tbody>
      ${b.map(x=>`<tr><td>${x.id}</td><td><strong>${x.name}</strong></td><td>${dm[x.division_id]||"—"}</td>
        <td><button class="btn btn-danger" onclick="delBat(${x.id})">Delete</button></td></tr>`).join("")}
      </tbody></table>`:'<p class="no-data">No batches yet</p>';
  }catch(e){$("bList").innerHTML=`<p class="no-data">${e.message}</p>`}
}
window.delBat=async id=>{if(!confirm("Delete?"))return;await api(`/api/batches/${id}`,"DELETE");loadBats()};

/* ============ CONSTRAINTS ============ */
ROUTES.constraints=async()=>{
  $("pageTitle").textContent="Manage Constraints";
  $("content").innerHTML=`
    <div class="card"><h2>Add Fixed Slot Constraint</h2>
      <p style="color:#6b7280;font-size:13px;margin-bottom:12px">Force a course to always appear at a specific time.</p>
      <form id="csForm"><div class="form-row">
        <div class="form-group"><label>Course Code</label><input id="csCode" placeholder="T&P" required></div>
        <div class="form-group"><label>Day</label><select id="csDay">${DAYS.map(d=>`<option>${d}</option>`).join("")}</select></div>
        <div class="form-group"><label>Start</label><input type="time" id="csStart" required></div>
        <div class="form-group"><label>End</label><input type="time" id="csEnd" required></div>
      </div><button class="btn btn-primary" style="width:auto;margin-top:12px">Add Constraint</button>
      <p class="error-msg" id="csErr"></p></form></div>
    <div class="card"><h2>Active Constraints</h2><div id="csList"></div></div>`;
  $("csForm").onsubmit=async e=>{
    e.preventDefault();
    try{
      await api("/api/constraints/","POST",{
        course_code:$("csCode").value,day:$("csDay").value,
        start_time:$("csStart").value,end_time:$("csEnd").value,is_active:1
      });
      e.target.reset();loadCs();
    }catch(err){$("csErr").textContent=err.message}
  };
  loadCs();
};
async function loadCs(){
  try{
    const c=await api("/api/constraints/");
    $("csList").innerHTML=c.length?`<table><thead><tr><th>Course</th><th>Day</th><th>Start</th><th>End</th><th>Action</th></tr></thead><tbody>
      ${c.map(x=>`<tr><td><strong>${x.course_code}</strong></td><td>${x.day}</td><td>${x.start_time}</td><td>${x.end_time}</td>
        <td><button class="btn btn-danger" onclick="delCs(${x.id})">Delete</button></td></tr>`).join("")}
      </tbody></table>`:'<p class="no-data">No constraints yet</p>';
  }catch(e){$("csList").innerHTML=`<p class="no-data">${e.message}</p>`}
}
window.delCs=async id=>{if(!confirm("Delete?"))return;await api(`/api/constraints/${id}`,"DELETE");loadCs()};

/* ============ TIMETABLE ============ */
async function buildTimetableHTML(isAdmin){
  const entries=await api("/api/timetable/");
  const [courses,teachers,rooms]=await Promise.all([
    api("/api/courses/").catch(()=>[]),api("/api/teachers/").catch(()=>[]),api("/api/rooms/").catch(()=>[])
  ]);
  const cm={},tm={},rm={};
  courses.forEach(c=>cm[c.id]=c);teachers.forEach(t=>tm[t.id]=t);rooms.forEach(r=>rm[r.id]=r);

  if(!entries.length)return '<p class="no-data">No timetable generated yet.</p>';

  const SLOTS2 = [
    { start: "09:00", end: "10:00", label: "09:00-10:00", span: 1 },
    { start: "10:00", end: "11:00", label: "10:00-11:00", span: 1 },
    { start: "11:15", end: "13:15", label: "11:15-13:15", span: 2 },
    { start: "14:00", end: "15:00", label: "14:00-15:00", span: 1 },
    { start: "15:00", end: "16:00", label: "15:00-16:00", span: 1 },
    { start: "16:00", end: "17:00", label: "16:00-17:00", span: 1 }
  ];

  const rendered = new Set();
  let rows = "";

  for (let i = 0; i < SLOTS2.length; i++) {
    const slot = SLOTS2[i];
    const cells = [];

    for (const day of DAYS) {
      const key = `${day}-${slot.start}`;
      if (rendered.has(key)) continue;

      let cellEntries = entries.filter(e => e.day === day && e.start_time === slot.start);

      if (slot.span === 2) {
        const midEntries = entries.filter(e => e.day === day && e.start_time === "12:15");
        cellEntries = [...cellEntries, ...midEntries];
        rendered.add(`${day}-12:15`);
      }

      if (!cellEntries.length) {
        cells.push('<td></td>');
        continue;
      }

      const content = cellEntries.map(e => {
        const c = cm[e.course_id] || {};
        const t = tm[e.teacher_id] || {};
        const r = rm[e.room_id] || {};
        const batch = e.batch ? ` (${e.batch})` : "";
        const timeRange = `${e.start_time}-${e.end_time}`;
        return `<div class="slot">
          <span class="cname">${c.code||"?"} — ${c.name||"?"}${batch}</span>
          <span class="tname">👤 ${t.name||"?"}</span>
          <span class="rname">🏫 ${r.name||"?"}</span>
          <span class="ttime">🕐 ${timeRange}</span>
        </div>`;
      }).join("");

      cells.push(`<td rowspan="${slot.span}" class="merged-cell">${content}</td>`);
    }

    if (cells.length) {
      rows += `<tr><td class="time-col">${slot.label}</td>${cells.join("")}</tr>`;
    }
  }

  return `<div class="tt-wrap"><table class="tt-table">
    <thead><tr><th>Time</th>${DAYS.map(d=>`<th>${d}</th>`).join("")}</tr></thead>
    <tbody>${rows}</tbody></table></div>
    <div style="text-align:center;margin-top:18px">
      <button class="btn btn-primary" style="width:auto" onclick="downloadPDF()">📄 Download PDF</button>
    </div>`;
}

ROUTES.timetable=async()=>{
  $("pageTitle").textContent="Weekly Timetable";
  $("content").innerHTML=`
    <div class="actions">
      <button class="btn btn-success" onclick="autoGenerate()" id="genBtn">⚡ Auto-Generate Timetable</button>
    </div>
    <div id="genMsg"></div>
    <div id="ttBody"><p class="no-data">Loading...</p></div>`;
  try{$("ttBody").innerHTML=await buildTimetableHTML(true)}
  catch(e){$("ttBody").innerHTML=`<p class="no-data">${e.message}</p>`}
};

window.autoGenerate=async()=>{
  if(!confirm("This will regenerate the timetable (locked slots preserved). Continue?"))return;
  const btn=$("genBtn");btn.disabled=true;btn.textContent="Generating...";
  try{
    const r=await api("/api/timetable/auto-generate","POST");
    $("genMsg").innerHTML=`<div class="msg-success">✅ ${r.message} — Placed ${r.placed}/${r.total_courses} courses.${r.unplaced_count>0?' ⚠️ Unplaced: '+r.unplaced.join(', '):''}</div>`;
    $("ttBody").innerHTML=await buildTimetableHTML(true);
  }catch(e){$("genMsg").innerHTML=`<div class="msg-error">❌ ${e.message}</div>`}
  finally{btn.disabled=false;btn.textContent="⚡ Auto-Generate Timetable"}
};

window.downloadPDF=async()=>{
  try{
    const r=await fetch(API+"/api/timetable/export/pdf",{headers:{Authorization:`Bearer ${getToken()}`}});
    if(!r.ok)throw new Error("Failed");
    const b=await r.blob();
    const u=URL.createObjectURL(b);
    const a=document.createElement("a");a.href=u;a.download="timetable.pdf";a.click();
    URL.revokeObjectURL(u);
  }catch(e){alert("PDF download failed: "+e.message)}
};

/* ============ STUDENT / TEACHER ============ */
ROUTES.studentTimetable=async()=>{
  $("pageTitle").textContent="My Timetable";
  const u=getUser();
  $("content").innerHTML=`<div class="card" style="margin-bottom:16px">
    <h2>👤 ${u.username}</h2>
    <p style="color:#6b7280;font-size:13px">${u.department||"—"} · Semester ${u.semester||"—"} · ${u.division||"—"} · Batch ${u.batch||"—"}</p>
  </div><div id="ttBody"><p class="no-data">Loading...</p></div>`;
  try{$("ttBody").innerHTML=await buildTimetableHTML(false)}
  catch(e){$("ttBody").innerHTML=`<p class="no-data">${e.message}</p>`}
};

ROUTES.teacherSchedule=async()=>{
  $("pageTitle").textContent="My Teaching Schedule";
  const u=getUser();
  $("content").innerHTML=`<div class="card" style="margin-bottom:16px">
    <h2>👨‍🏫 ${u.username}</h2>
    <p style="color:#6b7280;font-size:13px">Role: Teacher</p>
  </div><div id="ttBody"><p class="no-data">Loading...</p></div>`;
  try{$("ttBody").innerHTML=await buildTimetableHTML(false)}
  catch(e){$("ttBody").innerHTML=`<p class="no-data">${e.message}</p>`}
};

/* ============ PROFILE ============ */
ROUTES.profile=async()=>{
  const u=getUser();
  $("pageTitle").textContent="My Profile";
  const entries=await api("/api/timetable/").catch(()=>[]);
  const courses=await api("/api/courses/").catch(()=>[]);
  const rooms=await api("/api/rooms/").catch(()=>[]);
  $("content").innerHTML=`
    <div class="card" style="display:flex;align-items:center;gap:22px">
      <div style="width:90px;height:90px;border-radius:50%;background:linear-gradient(135deg,#5c6bc0,#3949ab);color:#fff;display:flex;align-items:center;justify-content:center;font-size:38px;font-weight:800">${(u.username||"U")[0].toUpperCase()}</div>
      <div style="flex:1">
        <h2 style="font-size:22px;margin-bottom:4px">${u.username}</h2>
        <p style="color:#6b7280;font-size:13px;margin-bottom:6px"><span class="badge">${u.role}</span></p>
        <p style="color:#6b7280;font-size:13px">${u.email||""}</p>
      </div>
    </div>
    <div class="stats-grid">
      ${card("Timetable Entries",entries.length)}
      ${card("Courses",courses.length)}
      ${card("Rooms",rooms.length)}
      ${card("Weekly Sessions",entries.length)}
    </div>
    <div class="card"><h2>👤 Personal Information</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px">
        ${infoCard("Full Name",u.username)}
        ${infoCard("Username",u.username)}
        ${infoCard("Email",u.email||"—")}
        ${infoCard("Role",u.role)}
        ${u.department?infoCard("Department",u.department):""}
        ${u.semester?infoCard("Semester",u.semester):""}
        ${u.division?infoCard("Division",u.division):""}
        ${u.batch?infoCard("Batch",u.batch):""}
      </div>
    </div>
    <div class="card"><h2>🎓 Academic Information</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px">
        ${infoCard("College","Kolhapur Institute of Technology")}
        ${infoCard("Academic Year","2026-2027")}
        ${infoCard("Status","Active")}
      </div>
    </div>`;
};
const infoCard=(l,v)=>`<div style="padding:14px;background:#f3f4f6;border-radius:10px;border-left:3px solid #5c6bc0">
  <label style="display:block;font-size:11px;text-transform:uppercase;color:#6b7280;font-weight:700;margin-bottom:4px">${l}</label>
  <p style="font-weight:600;color:#1f2937">${v}</p></div>`;

/* ============ INIT ============ */
function init(){
  const u=getUser();
  if(getToken()&&u){
    $("authScreen").classList.add("hidden");
    $("appScreen").classList.remove("hidden");
    buildNav();
    loadRegDepartments();
    const home=u.role==="admin"?"dashboard":u.role==="teacher"?"teacherSchedule":"studentTimetable";
    navigate(home);
  }else{
    $("authScreen").classList.remove("hidden");
    $("appScreen").classList.add("hidden");
    loadRegDepartments();
    toggleRoleFields();
  }
}
init();