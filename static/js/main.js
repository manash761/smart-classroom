// ================= GLOBALS & STATE =================
let subjectsCache = []; // Cache loaded subjects for dropdowns

document.addEventListener("DOMContentLoaded", () => {
    // Set Header Date
    const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('header-date').innerText = new Date().toLocaleDateString('en-US', dateOptions);
    
    if (USER_ROLE === 'teacher') {
        const dateInput = document.getElementById('attendance-date');
        if (dateInput) {
            dateInput.value = getTodayDateString();
        }
        // Load subjects first, then load the initial tab
        loadSubjectsIntoDropdowns().then(() => {
            switchTab('overview');
        });
    } else {
        switchTab('student-attendance');
    }

    // Set up file input listener for notes modal
    const fileInput = document.querySelector('.file-input');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const fileName = e.target.files[0]?.name || "Drag & drop files or click to upload";
            document.querySelector('.file-msg').innerText = fileName;
        });
    }
});

// ================= SUBJECTS LOADER =================
async function loadSubjectsIntoDropdowns() {
    try {
        const res = await fetch('/api/subjects');
        subjectsCache = await res.json();

        // Populate attendance subject selector
        const attendanceSelect = document.getElementById('attendance-subject');
        if (attendanceSelect) {
            attendanceSelect.innerHTML = '';
            subjectsCache.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.name;
                attendanceSelect.appendChild(opt);
            });
        }

        // Populate note subject selector
        const noteSelect = document.getElementById('note-subject');
        if (noteSelect) {
            noteSelect.innerHTML = '';
            subjectsCache.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.name;
                noteSelect.appendChild(opt);
            });
        }

        // Populate assignment subject selector
        const assignmentSelect = document.getElementById('assignment-subject');
        if (assignmentSelect) {
            assignmentSelect.innerHTML = '';
            subjectsCache.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.name;
                assignmentSelect.appendChild(opt);
            });
        }
    } catch (err) {
        showToast("Could not load subjects", "error");
    }
}

// Helper: Get YYYY-MM-DD date string
function getTodayDateString() {
    const today = new Date();
    const yyyy = today.getFullYear();
    let mm = today.getMonth() + 1;
    let dd = today.getDate();
    
    if (mm < 10) mm = '0' + mm;
    if (dd < 10) dd = '0' + dd;
    
    return `${yyyy}-${mm}-${dd}`;
}

// ================= TOAST SYSTEM =================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-text">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ================= TAB NAVIGATION =================
function switchTab(tabId) {
    // 1. Update Navigation Buttons
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('data-tab') === tabId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // 2. Hide/Show Panels
    const panels = document.querySelectorAll('.tab-panel');
    panels.forEach(panel => {
        panel.classList.remove('active');
    });

    let targetPanelId = `panel-${tabId}`;
    const targetPanel = document.getElementById(targetPanelId);
    if (targetPanel) {
        targetPanel.classList.add('active');
    }

    // 3. Update Title in Top Bar
    const titles = {
        'overview': 'Classroom Overview',
        'attendance': 'Mark Class Attendance',
        'notes': 'Lecture Notes & Materials',
        'assignments': 'Manage Assignments',
        'notices': 'Classroom Bulletin Board',
        'student-attendance': 'My Attendance Record',
        'student-notes': 'Study Resources',
        'student-assignments': 'My Class Assignments',
        'student-notices': 'Announcements'
    };
    document.getElementById('current-tab-title').innerText = titles[tabId] || 'Dashboard';

    // 4. Trigger API data loading for the selected tab
    triggerDataLoader(tabId);
}

// Trigger specific loaders
function triggerDataLoader(tabId) {
    if (tabId === 'overview') {
        loadStats();
        loadRoster();
    } else if (tabId === 'attendance') {
        loadAttendanceSheet();
    } else if (tabId === 'notes') {
        loadNotes();
    } else if (tabId === 'assignments') {
        loadAssignments();
    } else if (tabId === 'notices') {
        loadNotices();
    } else if (tabId === 'student-attendance') {
        loadStudentAttendance();
    } else if (tabId === 'student-notes') {
        loadStudentNotes();
    } else if (tabId === 'student-assignments') {
        loadStudentAssignments();
    } else if (tabId === 'student-notices') {
        loadStudentNotices();
    }
}

function getTeacherFilterQuery(source) {
    const semesterEl = document.getElementById(`${source}-semester`);
    const departmentEl = document.getElementById(`${source}-department`);
    const params = new URLSearchParams();

    if (semesterEl && semesterEl.value) params.set('semester', semesterEl.value);
    if (departmentEl && departmentEl.value) params.set('department', departmentEl.value);

    return params;
}

function getAttendanceCategoryClass(category) {
    if (category === 'Dis Collegiate') return 'category-dis';
    if (category === 'Non Collegiate') return 'category-non';
    return 'category-good';
}

function refreshTeacherOverview() {
    loadStats();
    loadRoster();
}

// ================= MODAL OPERATIONS =================
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    const form = document.querySelector(`#${modalId} form`);
    if (form) {
        form.reset();
        const fileMsg = form.querySelector('.file-msg');
        if (fileMsg) fileMsg.innerText = "Drag & drop files or click to upload";
    }
}

// ================= TEACHER DASHBOARD API WORKFLOWS =================

// Load stats widgets
async function loadStats() {
    try {
        const params = getTeacherFilterQuery('roster');
        const res = await fetch(`/api/stats${params.toString() ? `?${params.toString()}` : ''}`);
        const stats = await res.json();
        
        document.getElementById('stat-total-students').innerText = stats.total_students;
        document.getElementById('stat-attendance-avg').innerText = `${stats.class_attendance_average}%`;
        document.getElementById('stat-total-notices').innerText = stats.total_notices;
    } catch (err) {
        showToast("Error loading classroom statistics", "error");
    }
}

// Load student roster details
let rosterStudentsCache = [];
async function loadRoster() {
    try {
        const params = getTeacherFilterQuery('roster');
        const res = await fetch(`/api/students${params.toString() ? `?${params.toString()}` : ''}`);
        rosterStudentsCache = await res.json();
        renderRosterTable(rosterStudentsCache);
    } catch (err) {
        showToast("Error loading student roster", "error");
    }
}

function renderRosterTable(students) {
    const tbody = document.getElementById('roster-table-body');
    tbody.innerHTML = '';
    
    if (students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--color-text-muted);">No students found for this semester or department.</td></tr>`;
        return;
    }

    students.forEach(student => {
        let badgeClass = 'rate-good';
        if (student.attendance_rate < 75) badgeClass = 'rate-danger';
        else if (student.attendance_rate < 85) badgeClass = 'rate-warning';

        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-weight: 600;">${student.roll_number || 'N/A'}</td>
            <td style="font-weight: 500;">${student.name}</td>
            <td>${student.semester ? `Sem ${student.semester}` : 'N/A'}</td>
            <td>${student.department || 'N/A'}</td>
            <td>${student.present_classes} / ${student.total_classes} classes</td>
            <td>
                <span class="roster-rate-badge ${badgeClass}">${student.attendance_rate}%</span>
            </td>
            <td><span class="category-badge ${getAttendanceCategoryClass(student.attendance_category)}">${student.attendance_category}</span></td>
            <td>
                <div class="attendance-progress-bar">
                    <div class="progress-fill" style="width: ${student.attendance_rate}%; background-color: var(${badgeClass === 'rate-good' ? '--color-present' : (badgeClass === 'rate-warning' ? '--color-late' : '--color-absent')})"></div>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function filterRosterTable() {
    const q = document.getElementById('roster-search').value.toLowerCase();
    const filtered = rosterStudentsCache.filter(student => 
        student.name.toLowerCase().includes(q) || 
        (student.roll_number && student.roll_number.toLowerCase().includes(q))
    );
    renderRosterTable(filtered);
}

// Load attendance sheet for specific date & subject
async function loadAttendanceSheet() {
    const dateVal = document.getElementById('attendance-date').value;
    const subjectSelect = document.getElementById('attendance-subject');
    const subjectId = subjectSelect ? subjectSelect.value : '';
    const params = getTeacherFilterQuery('attendance');

    if (!dateVal) return;

    try {
        params.set('date', dateVal);
        if (subjectId) params.set('subject_id', subjectId);
        let url = `/api/attendance?${params.toString()}`;

        const res = await fetch(url);
        const data = await res.json();
        
        const tbody = document.getElementById('attendance-sheet-body');
        tbody.innerHTML = '';
        
        if (!data.students || data.students.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--color-text-muted); padding:20px;">No students found for this semester or department.</td></tr>`;
            return;
        }

        data.students.forEach(student => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-weight: 600;">${student.roll_number || 'N/A'}</td>
                <td style="font-weight: 500; text-align: left;">${student.name}</td>
                <td>${student.semester ? `Sem ${student.semester}` : 'N/A'}</td>
                <td>${student.department || 'N/A'}</td>
                <td colspan="3">
                    <div class="attendance-status-toggle" data-student-id="${student.student_id}">
                        <button type="button" class="toggle-btn present ${student.status === 'Present' ? 'active' : ''}" onclick="toggleStatus(this, 'Present')">Present</button>
                        <button type="button" class="toggle-btn absent ${student.status === 'Absent' ? 'active' : ''}" onclick="toggleStatus(this, 'Absent')">Absent</button>
                        <button type="button" class="toggle-btn late ${student.status === 'Late' ? 'active' : ''}" onclick="toggleStatus(this, 'Late')">Late</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        showToast("Error loading attendance sheet", "error");
    }
}

// Toggle attendance button states
function toggleStatus(btn, status) {
    const parent = btn.parentElement;
    const buttons = parent.querySelectorAll('.toggle-btn');
    buttons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

// Bulk mark operations
function markAllAttendance(status) {
    const toggles = document.querySelectorAll('.attendance-status-toggle');
    toggles.forEach(toggle => {
        const buttons = toggle.querySelectorAll('.toggle-btn');
        buttons.forEach(btn => {
            if (btn.classList.contains(status.toLowerCase())) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    });
    showToast(`Marked all students as ${status}`, 'info');
}

// Submit marked attendance data to backend
async function submitAttendance() {
    const dateVal = document.getElementById('attendance-date').value;
    const subjectSelect = document.getElementById('attendance-subject');
    const subjectId = subjectSelect ? subjectSelect.value : null;

    if (!subjectId) {
        showToast("Please select a subject before saving attendance", "error");
        return;
    }

    const toggles = document.querySelectorAll('.attendance-status-toggle');
    if (toggles.length === 0) {
        showToast("No students to record. Load the attendance sheet first.", "error");
        return;
    }
    
    const records = [];
    toggles.forEach(toggle => {
        const studentId = toggle.getAttribute('data-student-id');
        const activeBtn = toggle.querySelector('.toggle-btn.active');
        const status = activeBtn ? activeBtn.innerText.trim() : 'Absent';
        records.push({ student_id: parseInt(studentId), status: status });
    });

    try {
        const res = await fetch('/api/attendance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date: dateVal, subject_id: parseInt(subjectId), records: records })
        });
        
        if (res.ok) {
            showToast(`Attendance for ${dateVal} successfully recorded`, 'success');
            loadAttendanceSheet();
        } else {
            const err = await res.json();
            showToast(err.error || "Failed to submit attendance", "error");
        }
    } catch (err) {
        showToast("Network error submitting records", "error");
    }
}

// Load lecture notes
async function loadNotes() {
    try {
        const res = await fetch('/api/notes');
        const notes = await res.json();
        const grid = document.getElementById('notes-grid');
        grid.innerHTML = '';

        if (notes.length === 0) {
            grid.innerHTML = `<div class="glass-container" style="grid-column: 1/-1; text-align: center; color: var(--color-text-muted);">No study materials shared yet.</div>`;
            return;
        }

        notes.forEach(note => {
            const card = document.createElement('div');
            card.className = 'resource-card';
            
            let downloadBtnHTML = '';
            if (note.file_path) {
                downloadBtnHTML = `
                    <a href="/${note.file_path}" class="btn-download" target="_blank">
                        <span>📥 Download Document</span>
                    </a>
                `;
            } else {
                downloadBtnHTML = `<span style="text-align:center; font-size: 0.8rem; color: var(--color-text-muted);">No attached file</span>`;
            }

            card.innerHTML = `
                <div class="card-top">
                    <span class="resource-badge">${note.subject_name || 'Notes'}</span>
                    <h4>${note.title}</h4>
                    <p class="resource-desc">${note.description || 'No description provided.'}</p>
                </div>
                <div class="card-bottom">
                    <div class="meta-row">
                        <span>By ${note.author}</span>
                        <span>${formatDateString(note.created_at)}</span>
                    </div>
                    ${downloadBtnHTML}
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (err) {
        showToast("Error loading lecture resources", "error");
    }
}

// Submit Notes Upload Form
async function submitNoteForm(e) {
    e.preventDefault();
    const title = document.getElementById('note-title').value;
    const description = document.getElementById('note-desc').value;
    const subjectId = document.getElementById('note-subject').value;
    const fileInput = document.getElementById('note-file');

    if (!subjectId) {
        showToast("Please select a subject", "error");
        return;
    }
    
    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('subject_id', subjectId);
    if (fileInput.files[0]) {
        formData.append('file', fileInput.files[0]);
    }

    try {
        const res = await fetch('/api/notes', {
            method: 'POST',
            body: formData
        });
        
        if (res.ok) {
            showToast("Lecture notes uploaded successfully!", "success");
            closeModal('notes-modal');
            loadNotes();
        } else {
            const err = await res.json();
            showToast(err.error || "Failed to upload notes", "error");
        }
    } catch (err) {
        showToast("Network error during file upload", "error");
    }
}

// Load assignments list
async function loadAssignments() {
    try {
        const res = await fetch('/api/assignments');
        const assignments = await res.json();
        const grid = document.getElementById('assignments-grid');
        grid.innerHTML = '';

        if (assignments.length === 0) {
            grid.innerHTML = `<div class="glass-container" style="grid-column: 1/-1; text-align: center; color: var(--color-text-muted);">No assignments created.</div>`;
            return;
        }

        assignments.forEach(asg => {
            const card = document.createElement('div');
            card.className = 'resource-card';
            
            const dueStr = formatDateString(asg.due_date);
            const isOverdue = new Date(asg.due_date) < new Date();
            const badgeClass = isOverdue ? 'due-danger' : 'status-late';

            card.innerHTML = `
                <div class="card-top">
                    <span class="resource-badge" style="background: rgba(20, 184, 166, 0.15); color: var(--accent-teal); border-color: rgba(20, 184, 166, 0.3);">${asg.subject_name || 'Assignment'}</span>
                    <h4>${asg.title}</h4>
                    <p class="resource-desc">${asg.description || 'No description provided.'}</p>
                </div>
                <div class="card-bottom">
                    <div class="meta-row">
                        <span>Issued by ${asg.author}</span>
                        <span>Created: ${formatDateString(asg.created_at)}</span>
                    </div>
                    <div class="meta-row" style="margin-top: 4px;">
                        <span>Due Date:</span>
                        <span class="due-badge ${badgeClass}">${dueStr}</span>
                    </div>
                    <button class="btn btn-danger btn-card-action" onclick="deleteAssignment(${asg.id})">Delete Assignment</button>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (err) {
        showToast("Error loading assignments", "error");
    }
}

async function deleteAssignment(assignmentId) {
    if (!confirm('Delete this assignment?')) return;

    try {
        const res = await fetch(`/api/assignments/${assignmentId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
            showToast('Assignment deleted successfully', 'success');
            loadAssignments();
        } else {
            showToast(data.error || 'Failed to delete assignment', 'error');
        }
    } catch (err) {
        showToast('Network error deleting assignment', 'error');
    }
}

// Submit Assignment Posting Form
async function submitAssignmentForm(e) {
    e.preventDefault();
    const title = document.getElementById('assignment-title').value;
    const description = document.getElementById('assignment-desc').value;
    const due_date = document.getElementById('assignment-due').value;
    const subject_id = document.getElementById('assignment-subject').value;

    if (!subject_id) {
        showToast("Please select a subject", "error");
        return;
    }

    try {
        const res = await fetch('/api/assignments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, due_date, subject_id: parseInt(subject_id) })
        });
        
        if (res.ok) {
            showToast("New assignment created successfully!", "success");
            closeModal('assignments-modal');
            loadAssignments();
        } else {
            const err = await res.json();
            showToast(err.error || "Failed to create assignment", "error");
        }
    } catch (err) {
        showToast("Network error publishing assignment", "error");
    }
}

// Load notice bulletin board
async function loadNotices() {
    try {
        const res = await fetch('/api/notices');
        const notices = await res.json();
        const list = document.getElementById('notices-list');
        list.innerHTML = '';

        if (notices.length === 0) {
            list.innerHTML = `<div class="glass-container" style="text-align: center; color: var(--color-text-muted);">No notifications posted.</div>`;
            return;
        }

        notices.forEach(notice => {
            const card = document.createElement('div');
            card.className = 'bulletin-card';
            card.innerHTML = `
                <div class="bulletin-header">
                    <h4>${notice.title}</h4>
                    <div class="bulletin-meta">
                        <span>Posted by ${notice.author}</span>
                        <span style="margin: 0 8px;">•</span>
                        <span>${formatDateString(notice.created_at)}</span>
                    </div>
                </div>
                <div class="bulletin-body">${notice.content}</div>
                <button class="btn btn-danger btn-card-action" onclick="deleteNotice(${notice.id})">Delete Notice</button>
            `;
            list.appendChild(card);
        });
    } catch (err) {
        showToast("Error loading bulletin board", "error");
    }
}

async function deleteNotice(noticeId) {
    if (!confirm('Delete this notice?')) return;

    try {
        const res = await fetch(`/api/notices/${noticeId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
            showToast('Notice deleted successfully', 'success');
            loadNotices();
        } else {
            showToast(data.error || 'Failed to delete notice', 'error');
        }
    } catch (err) {
        showToast('Network error deleting notice', 'error');
    }
}

// Submit Notices Posting Form
async function submitNoticeForm(e) {
    e.preventDefault();
    const title = document.getElementById('notice-title').value;
    const content = document.getElementById('notice-content').value;

    try {
        const res = await fetch('/api/notices', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content })
        });
        
        if (res.ok) {
            showToast("Notice posted to bulletin successfully!", "success");
            closeModal('notices-modal');
            loadNotices();
        } else {
            const err = await res.json();
            showToast(err.error || "Failed to post notice", "error");
        }
    } catch (err) {
        showToast("Network error posting announcement", "error");
    }
}

// ================= STUDENT DASHBOARD API WORKFLOWS =================

// Load student personal attendance stats and list
async function loadStudentAttendance() {
    try {
        const res = await fetch('/api/attendance');
        const data = await res.json();
        
        // 1. Update Stats numbers
        document.getElementById('student-classes-present').innerText = data.present_classes;
        document.getElementById('student-classes-total').innerText = data.total_classes;
        
        // 2. Animate Circular Progress Bar
        const pct = data.attendance_rate;
        document.getElementById('student-pct-text').innerText = `${pct}%`;
        
        const circle = document.getElementById('student-progress-circle');
        const radius = circle.r.baseVal.value;
        const circumference = 2 * Math.PI * radius; // 251.2
        const offset = circumference - (pct / 100) * circumference;
        circle.style.strokeDashoffset = offset;
        
        // Adjust circle color based on performance
        if (pct >= 85) circle.style.stroke = 'var(--color-present)';
        else if (pct >= 75) circle.style.stroke = 'var(--color-late)';
        else circle.style.stroke = 'var(--color-absent)';

        // 3. Render Per-Subject Breakdown Grid
        const subjectsGrid = document.getElementById('student-subjects-grid');
        if (subjectsGrid && data.subjects_stats) {
            subjectsGrid.innerHTML = '';
            data.subjects_stats.forEach(sub => {
                if (sub.total_classes === 0) return; // skip subjects with no classes

                let color = '#22c55e'; // green
                let bgColor = 'rgba(34,197,94,0.12)';
                let borderColor = 'rgba(34,197,94,0.25)';
                if (sub.attendance_rate < 60) {
                    color = '#ef4444'; bgColor = 'rgba(239,68,68,0.12)'; borderColor = 'rgba(239,68,68,0.25)';
                } else if (sub.attendance_rate < 75) {
                    color = '#f59e0b'; bgColor = 'rgba(245,158,11,0.12)'; borderColor = 'rgba(245,158,11,0.25)';
                }

                const subCard = document.createElement('div');
                subCard.style.cssText = `
                    background: ${bgColor};
                    border: 1px solid ${borderColor};
                    border-radius: 14px;
                    padding: 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                `;
                subCard.innerHTML = `
                    <div style="font-size:0.78rem; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.05em;">
                        ${sub.subject_name}
                    </div>
                    <div style="font-size:1.8rem; font-weight:800; color:${color}; line-height:1;">${sub.attendance_rate}%</div>
                    <div style="font-size:0.8rem; color:#94a3b8;">${sub.present_classes} / ${sub.total_classes} classes attended</div>
                    <div class="category-badge ${getAttendanceCategoryClass(sub.attendance_category)}" style="align-self:flex-start;">${sub.attendance_category}</div>
                    <div style="background: rgba(255,255,255,0.06); border-radius: 6px; height: 6px; overflow:hidden;">
                        <div style="height:100%; width:${sub.attendance_rate}%; background:${color}; border-radius:6px; transition: width 0.8s ease;"></div>
                    </div>
                `;
                subjectsGrid.appendChild(subCard);
            });

            if (subjectsGrid.children.length === 0) {
                subjectsGrid.innerHTML = `<p style="color:#64748b; font-size:0.85rem;">No subject-wise records yet.</p>`;
            }
        }

        // 4. Render Detailed Logs
        const tbody = document.getElementById('student-attendance-body');
        tbody.innerHTML = '';

        if (data.records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--color-text-muted);">No attendance records found.</td></tr>`;
            return;
        }

        data.records.forEach(record => {
            let badgeClass = 'status-present';
            if (record.status === 'Absent') badgeClass = 'status-absent';
            else if (record.status === 'Late') badgeClass = 'status-late';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="font-weight: 500;">${formatDateString(record.attendance_date)}</td>
                <td style="color: #94a3b8;">${record.subject_name || '—'}</td>
                <td>
                    <span class="attendance-status-label ${badgeClass}">${record.status}</span>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (err) {
        showToast("Error loading attendance data", "error");
    }
}

// Load study resources (Student)
async function loadStudentNotes() {
    try {
        const res = await fetch('/api/notes');
        const notes = await res.json();
        const grid = document.getElementById('student-notes-grid');
        grid.innerHTML = '';

        if (notes.length === 0) {
            grid.innerHTML = `<div class="glass-container" style="grid-column: 1/-1; text-align: center; color: var(--color-text-muted);">No shared notes or documents.</div>`;
            return;
        }

        notes.forEach(note => {
            const card = document.createElement('div');
            card.className = 'resource-card';
            
            let downloadBtnHTML = '';
            if (note.file_path) {
                downloadBtnHTML = `
                    <a href="/${note.file_path}" class="btn-download" target="_blank">
                        <span>📥 Download Document</span>
                    </a>
                `;
            } else {
                downloadBtnHTML = `<span style="text-align:center; font-size: 0.8rem; color: var(--color-text-muted);">No attached file</span>`;
            }

            card.innerHTML = `
                <div class="card-top">
                    <span class="resource-badge">${note.subject_name || 'Notes'}</span>
                    <h4>${note.title}</h4>
                    <p class="resource-desc">${note.description || 'No description provided.'}</p>
                </div>
                <div class="card-bottom">
                    <div class="meta-row">
                        <span>By ${note.author}</span>
                        <span>${formatDateString(note.created_at)}</span>
                    </div>
                    ${downloadBtnHTML}
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (err) {
        showToast("Error loading lecture study materials", "error");
    }
}

// Load assignments (Student)
async function loadStudentAssignments() {
    try {
        const res = await fetch('/api/assignments');
        const assignments = await res.json();
        const grid = document.getElementById('student-assignments-grid');
        grid.innerHTML = '';

        if (assignments.length === 0) {
            grid.innerHTML = `<div class="glass-container" style="grid-column: 1/-1; text-align: center; color: var(--color-text-muted);">No active assignments. Enjoy your free time!</div>`;
            return;
        }

        assignments.forEach(asg => {
            const card = document.createElement('div');
            card.className = 'resource-card';
            
            const dueStr = formatDateString(asg.due_date);
            const isOverdue = new Date(asg.due_date) < new Date();
            const badgeClass = isOverdue ? 'due-danger' : 'status-late';

            card.innerHTML = `
                <div class="card-top">
                    <span class="resource-badge" style="background: rgba(20, 184, 166, 0.15); color: var(--accent-teal); border-color: rgba(20, 184, 166, 0.3);">${asg.subject_name || 'Assignment'}</span>
                    <h4>${asg.title}</h4>
                    <p class="resource-desc">${asg.description || 'No instruction details provided.'}</p>
                </div>
                <div class="card-bottom">
                    <div class="meta-row">
                        <span>Issued by ${asg.author}</span>
                        <span>Issued: ${formatDateString(asg.created_at)}</span>
                    </div>
                    <div class="meta-row" style="margin-top: 4px;">
                        <span>Submit Before:</span>
                        <span class="due-badge ${badgeClass}">${dueStr}</span>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (err) {
        showToast("Error loading assignments", "error");
    }
}

// Load notices (Student)
async function loadStudentNotices() {
    try {
        const res = await fetch('/api/notices');
        const notices = await res.json();
        const list = document.getElementById('student-notices-list');
        list.innerHTML = '';

        if (notices.length === 0) {
            list.innerHTML = `<div class="glass-container" style="text-align: center; color: var(--color-text-muted);">No notices posted.</div>`;
            return;
        }

        notices.forEach(notice => {
            const card = document.createElement('div');
            card.className = 'bulletin-card';
            card.innerHTML = `
                <div class="bulletin-header">
                    <h4>${notice.title}</h4>
                    <div class="bulletin-meta">
                        <span>Posted by ${notice.author}</span>
                        <span style="margin: 0 8px;">•</span>
                        <span>${formatDateString(notice.created_at)}</span>
                    </div>
                </div>
                <div class="bulletin-body">${notice.content}</div>
            `;
            list.appendChild(card);
        });
    } catch (err) {
        showToast("Error loading notices", "error");
    }
}

// ================= UTILITIES =================
function formatDateString(dateStr) {
    if (!dateStr) return 'N/A';
    
    // SQLite can store timestamps; grab date portion only
    const cleanDateStr = dateStr.includes(' ') ? dateStr.split(' ')[0] : dateStr;
    const dateObj = new Date(cleanDateStr + 'T00:00:00'); // Force local timezone
    
    if (isNaN(dateObj.getTime())) return dateStr;
    
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return dateObj.toLocaleDateString('en-US', options);
}
