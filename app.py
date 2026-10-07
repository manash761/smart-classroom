from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import datetime
from database import execute_query, init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smart_classroom_secret_key_2026')

DEPARTMENTS = (
    "Computer Science Department",
    "Electrical Department",
    "Printing Technology",
)
SEMESTERS = tuple(range(1, 7))

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'notes')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Initialize database on startup
with app.app_context():
    init_db()

# Helper decorator for login required
def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return jsonify({"error": "Unauthorized access"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Page Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')  # 'teacher', 'student', or 'admin'
        
        user = execute_query(
            "SELECT * FROM users WHERE username = %s AND role = %s", 
            (username, role), 
            fetch='one'
        )
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            session['roll_number'] = user['roll_number']
            session['semester'] = user.get('semester')
            session['department'] = user.get('department')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials or role. Please try again.", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_panel'))
    return render_template('dashboard.html', name=session.get('name'), role=session.get('role'))

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    return render_template('admin.html', name=session.get('name'))

# --- API Endpoints ---

@app.route('/api/profile', methods=['GET'])
@login_required()
def get_profile():
    return jsonify({
        "id": session.get('user_id'),
        "username": session.get('username'),
        "role": session.get('role'),
        "name": session.get('name'),
        "roll_number": session.get('roll_number'),
        "semester": session.get('semester'),
        "department": session.get('department')
    })

def attendance_category(rate):
    if rate < 60:
        return "Dis Collegiate"
    if rate < 75:
        return "Non Collegiate"
    return "Collegiate"

def build_student_filter_clause():
    semester = request.args.get('semester')
    department = request.args.get('department')
    clauses = ["role = 'student'"]
    params = []

    if semester:
        clauses.append("semester = %s")
        params.append(int(semester))
    if department:
        clauses.append("department = %s")
        params.append(department)

    return " AND ".join(clauses), tuple(params)

# 0. Subjects API
@app.route('/api/subjects', methods=['GET'])
@login_required()
def get_subjects():
    if session.get('role') == 'teacher':
        subjects = execute_query(
            "SELECT id, name FROM subjects WHERE teacher_id = %s ORDER BY name",
            (session.get('user_id'),),
            fetch='all'
        )
    else:
        # Students and admin see all subjects
        subjects = execute_query(
            "SELECT id, name FROM subjects ORDER BY name",
            fetch='all'
        )
    return jsonify(subjects)

# 1. Notices API
@app.route('/api/notices', methods=['GET', 'POST'])
@login_required()
def handle_notices():
    if request.method == 'GET':
        notices = execute_query(
            """SELECT n.*, u.name as author 
               FROM notices n 
               JOIN users u ON n.uploaded_by = u.id 
               ORDER BY n.created_at DESC""", 
            fetch='all'
        )
        return jsonify(notices)
        
    elif request.method == 'POST':
        if session.get('role') != 'teacher':
            return jsonify({"error": "Only teachers can post notices"}), 403
            
        data = request.json
        title = data.get('title')
        content = data.get('content')
        
        if not title or not content:
            return jsonify({"error": "Title and Content are required"}), 400
            
        execute_query(
            "INSERT INTO notices (title, content, uploaded_by) VALUES (%s, %s, %s)",
            (title, content, session.get('user_id'))
        )
        return jsonify({"message": "Notice posted successfully"}), 201

@app.route('/api/notices/<int:notice_id>', methods=['DELETE'])
@login_required('teacher')
def delete_notice(notice_id):
    notice = execute_query(
        "SELECT id, uploaded_by FROM notices WHERE id = %s",
        (notice_id,),
        fetch='one'
    )
    if not notice:
        return jsonify({"error": "Notice not found"}), 404
    if notice['uploaded_by'] != session.get('user_id'):
        return jsonify({"error": "You can only delete notices you posted"}), 403

    execute_query("DELETE FROM notices WHERE id = %s", (notice_id,))
    return jsonify({"message": "Notice deleted successfully"}), 200

# 2. Assignments API
@app.route('/api/assignments', methods=['GET', 'POST'])
@login_required()
def handle_assignments():
    if request.method == 'GET':
        assignments = execute_query(
            """SELECT a.*, u.name as author, s.name as subject_name 
               FROM assignments a 
               JOIN users u ON a.uploaded_by = u.id 
               JOIN subjects s ON a.subject_id = s.id
               ORDER BY a.created_at DESC""", 
            fetch='all'
        )
        return jsonify(assignments)
        
    elif request.method == 'POST':
        if session.get('role') != 'teacher':
            return jsonify({"error": "Only teachers can post assignments"}), 403
            
        data = request.json
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        subject_id = data.get('subject_id')
        
        if not title or not due_date or not subject_id:
            return jsonify({"error": "Title, Due Date, and Subject are required"}), 400
            
        execute_query(
            "INSERT INTO assignments (title, description, due_date, uploaded_by, subject_id) VALUES (%s, %s, %s, %s, %s)",
            (title, description, due_date, session.get('user_id'), int(subject_id))
        )
        return jsonify({"message": "Assignment created successfully"}), 201

@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
@login_required('teacher')
def delete_assignment(assignment_id):
    assignment = execute_query(
        "SELECT id, uploaded_by FROM assignments WHERE id = %s",
        (assignment_id,),
        fetch='one'
    )
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404
    if assignment['uploaded_by'] != session.get('user_id'):
        return jsonify({"error": "You can only delete assignments you created"}), 403

    execute_query("DELETE FROM assignments WHERE id = %s", (assignment_id,))
    return jsonify({"message": "Assignment deleted successfully"}), 200

# 3. Notes / Resources API
@app.route('/api/notes', methods=['GET', 'POST'])
@login_required()
def handle_notes():
    if request.method == 'GET':
        notes = execute_query(
            """SELECT n.*, u.name as author, s.name as subject_name 
               FROM notes n 
               JOIN users u ON n.uploaded_by = u.id 
               JOIN subjects s ON n.subject_id = s.id
               ORDER BY n.created_at DESC""", 
            fetch='all'
        )
        return jsonify(notes)
        
    elif request.method == 'POST':
        if session.get('role') != 'teacher':
            return jsonify({"error": "Only teachers can upload notes"}), 403
            
        title = request.form.get('title')
        description = request.form.get('description')
        subject_id = request.form.get('subject_id')
        
        if not title or not subject_id:
            return jsonify({"error": "Title and Subject are required"}), 400
            
        file = request.files.get('file')
        file_name = None
        file_path = None
        
        if file and file.filename != '':
            file_name = secure_filename(file.filename)
            # Add timestamp to avoid overwrites
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S_')
            saved_name = timestamp + file_name
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_name)
            file.save(save_path)
            file_path = f"static/uploads/notes/{saved_name}"
            
        execute_query(
            "INSERT INTO notes (title, description, file_name, file_path, uploaded_by, subject_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (title, description, file_name, file_path, session.get('user_id'), int(subject_id))
        )
        return jsonify({"message": "Notes uploaded successfully"}), 201

# 4. Students API (Teacher Only)
@app.route('/api/students', methods=['GET'])
@login_required('teacher')
def get_students():
    filter_clause, filter_params = build_student_filter_clause()
    students = execute_query(
        f"""SELECT id, username, name, roll_number, semester, department
            FROM users
            WHERE {filter_clause}
            ORDER BY department, semester, roll_number""",
        filter_params,
        fetch='all'
    )
    
    # Calculate attendance statistics for each student across all subjects
    for student in students:
        records = execute_query(
            "SELECT status FROM attendance WHERE student_id = %s",
            (student['id'],),
            fetch='all'
        )
        total = len(records)
        present = sum(1 for r in records if r['status'] in ('Present', 'Late'))
        
        student['total_classes'] = total
        student['present_classes'] = present
        student['attendance_rate'] = round((present / total) * 100) if total > 0 else 0
        student['attendance_category'] = attendance_category(student['attendance_rate'])
        
    return jsonify(students)

# 5. Attendance API
@app.route('/api/attendance', methods=['GET', 'POST'])
@login_required()
def handle_attendance():
    if request.method == 'GET':
        # If student: returns logs and subject-wise stats
        if session.get('role') == 'student':
            student_id = session.get('user_id')
            records = execute_query(
                """SELECT a.attendance_date, a.status, s.name as subject_name 
                   FROM attendance a 
                   JOIN subjects s ON a.subject_id = s.id 
                   WHERE a.student_id = %s 
                   ORDER BY a.attendance_date DESC""",
                (student_id,),
                fetch='all'
            )
            
            # Format dates to string
            formatted_records = []
            for r in records:
                date_val = r['attendance_date']
                date_str = date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val)
                formatted_records.append({
                    "attendance_date": date_str,
                    "status": r['status'],
                    "subject_name": r['subject_name']
                })
                
            # Fetch per-subject rates
            subjects = execute_query("SELECT id, name FROM subjects ORDER BY name", fetch='all')
            subjects_stats = []
            
            overall_total = 0
            overall_present = 0
            
            for sub in subjects:
                sub_records = execute_query(
                    "SELECT status FROM attendance WHERE student_id = %s AND subject_id = %s",
                    (student_id, sub['id']),
                    fetch='all'
                )
                total = len(sub_records)
                present = sum(1 for r in sub_records if r['status'] in ('Present', 'Late'))
                
                overall_total += total
                overall_present += present
                
                subjects_stats.append({
                    "subject_id": sub['id'],
                    "subject_name": sub['name'],
                    "total_classes": total,
                    "present_classes": present,
                    "attendance_rate": round((present / total) * 100) if total > 0 else 0,
                    "attendance_category": attendance_category(round((present / total) * 100) if total > 0 else 0)
                })
                
            overall_pct = round((overall_present / overall_total) * 100) if overall_total > 0 else 0
            
            return jsonify({
                "records": formatted_records,
                "subjects_stats": subjects_stats,
                "total_classes": overall_total,
                "present_classes": overall_present,
                "attendance_rate": overall_pct,
                "attendance_category": attendance_category(overall_pct)
            })
            
        # If teacher: returns students status on a specific date for a specific subject
        else:
            date_str = request.args.get('date')
            subject_id_str = request.args.get('subject_id')
            filter_clause, filter_params = build_student_filter_clause()
            
            if not date_str:
                date_str = datetime.date.today().strftime('%Y-%m-%d')
                
            if not subject_id_str:
                # Fallback: get first subject taught by teacher
                first_sub = execute_query(
                    "SELECT id FROM subjects WHERE teacher_id = %s LIMIT 1",
                    (session.get('user_id'),), fetch='one'
                )
                if first_sub:
                    subject_id = first_sub['id']
                else:
                    return jsonify({"date": date_str, "students": [], "subject_id": None})
            else:
                subject_id = int(subject_id_str)
                
            # Fetch all students
            students = execute_query(
                f"""SELECT id, name, roll_number, semester, department
                    FROM users
                    WHERE {filter_clause}
                    ORDER BY department, semester, roll_number""",
                filter_params,
                fetch='all'
            )
            
            # Fetch attendance for this date & subject
            attendance_records = execute_query(
                "SELECT student_id, status FROM attendance WHERE attendance_date = %s AND subject_id = %s",
                (date_str, subject_id),
                fetch='all'
            )
            
            status_map = {r['student_id']: r['status'] for r in attendance_records}
            
            result = []
            for student in students:
                result.append({
                    "student_id": student['id'],
                    "name": student['name'],
                    "roll_number": student['roll_number'],
                    "semester": student['semester'],
                    "department": student['department'],
                    "status": status_map.get(student['id'], 'Absent')  # Default to Absent if unmarked
                })
                
            return jsonify({
                "date": date_str,
                "subject_id": subject_id,
                "students": result
            })
            
    elif request.method == 'POST':
        if session.get('role') != 'teacher':
            return jsonify({"error": "Only teachers can mark attendance"}), 403
            
        data = request.json
        date_str = data.get('date')
        subject_id = data.get('subject_id')
        records = data.get('records')  # List of {student_id, status}
        
        if not date_str or not subject_id or not records:
            return jsonify({"error": "Date, Subject, and records are required"}), 400
            
        try:
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
        for record in records:
            student_id = record.get('student_id')
            status = record.get('status')
            
            if status not in ('Present', 'Absent', 'Late'):
                continue
                
            # Database-agnostic upsert: DELETE first, then INSERT
            execute_query(
                "DELETE FROM attendance WHERE student_id = %s AND subject_id = %s AND attendance_date = %s",
                (student_id, int(subject_id), target_date)
            )
            execute_query(
                "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (%s, %s, %s, %s)",
                (student_id, int(subject_id), target_date, status)
            )
            
        return jsonify({"message": f"Attendance for {date_str} updated successfully"}), 200

# 6. Overall Stats API (Teacher Only)
@app.route('/api/stats', methods=['GET'])
@login_required('teacher')
def get_stats():
    filter_clause, filter_params = build_student_filter_clause()
    total_students = execute_query(
        f"SELECT COUNT(*) as count FROM users WHERE {filter_clause}",
        filter_params,
        fetch='one'
    )['count']
    
    total_notices = execute_query(
        "SELECT COUNT(*) as count FROM notices",
        fetch='one'
    )['count']
    
    # Calculate overall class attendance average
    total_records = execute_query(
        f"""SELECT COUNT(*) as count
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            WHERE {filter_clause}""",
        filter_params,
        fetch='one'
    )['count']
    
    present_records = execute_query(
        f"""SELECT COUNT(*) as count
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            WHERE {filter_clause} AND a.status IN ('Present', 'Late')""",
        filter_params,
        fetch='one'
    )['count']
    
    class_average = round((present_records / total_records) * 100) if total_records > 0 else 0
    
    return jsonify({
        "total_students": total_students,
        "total_notices": total_notices,
        "class_attendance_average": class_average
    })

# ============================================================
# ADMIN API ENDPOINTS
# ============================================================

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        if session.get('role') != 'admin':
            return jsonify({"error": "Administrator access required"}), 403
        return f(*args, **kwargs)
    return decorated

# Admin: List/Create Users
@app.route('/api/admin/users', methods=['GET', 'POST'])
@admin_required
def admin_users():
    if request.method == 'GET':
        users = execute_query(
            """SELECT id, username, name, role, roll_number, semester, department
               FROM users
               WHERE role != 'admin'
               ORDER BY role, department, semester, name""",
            fetch='all'
        )
        return jsonify(users)

    elif request.method == 'POST':
        data = request.json
        name = data.get('name', '').strip()
        username = data.get('username', '').strip()
        role = data.get('role', '').strip()
        password = data.get('password', '')
        roll_number = data.get('roll_number', None)
        semester = data.get('semester', None)
        department = data.get('department', None)

        if not name or not username or not role or not password:
            return jsonify({"error": "Name, username, role, and password are required"}), 400

        if role not in ('student', 'teacher'):
            return jsonify({"error": "Role must be 'student' or 'teacher'"}), 400

        if role == 'student':
            if not semester or int(semester) not in SEMESTERS:
                return jsonify({"error": "Students must have a semester from 1 to 6"}), 400
            if department not in DEPARTMENTS:
                return jsonify({"error": "Students must have a valid department"}), 400
        else:
            semester = None
            department = None

        # Check for duplicate username
        existing = execute_query("SELECT id FROM users WHERE username = %s", (username,), fetch='one')
        if existing:
            return jsonify({"error": f"Username '{username}' already exists"}), 409

        # Roll number uniqueness for students
        if role == 'student' and roll_number:
            dup_roll = execute_query("SELECT id FROM users WHERE roll_number = %s", (roll_number,), fetch='one')
            if dup_roll:
                return jsonify({"error": f"Roll number '{roll_number}' already in use"}), 409

        execute_query(
            """INSERT INTO users (username, password_hash, role, name, roll_number, semester, department)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                username,
                generate_password_hash(password),
                role,
                name,
                roll_number if role == 'student' else None,
                int(semester) if role == 'student' else None,
                department if role == 'student' else None,
            )
        )
        return jsonify({"message": f"User '{name}' created successfully"}), 201

# Admin: Delete / Update User
@app.route('/api/admin/users/<int:user_id>', methods=['DELETE', 'PUT'])
@admin_required
def admin_user_detail(user_id):
    if request.method == 'DELETE':
        user = execute_query("SELECT id, role FROM users WHERE id = %s", (user_id,), fetch='one')
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user['role'] == 'admin':
            return jsonify({"error": "Cannot delete admin accounts"}), 403

        # Cascade delete related records
        execute_query("DELETE FROM attendance WHERE student_id = %s", (user_id,))
        execute_query("DELETE FROM notes WHERE uploaded_by = %s", (user_id,))
        execute_query("DELETE FROM assignments WHERE uploaded_by = %s", (user_id,))
        execute_query("DELETE FROM notices WHERE uploaded_by = %s", (user_id,))
        execute_query("DELETE FROM users WHERE id = %s", (user_id,))

        return jsonify({"message": "User deleted successfully"}), 200

    elif request.method == 'PUT':
        data = request.json
        name = data.get('name', '').strip()
        password = data.get('password', '').strip()

        if name:
            execute_query("UPDATE users SET name = %s WHERE id = %s", (name, user_id))
        if password:
            execute_query("UPDATE users SET password_hash = %s WHERE id = %s",
                          (generate_password_hash(password), user_id))

        return jsonify({"message": "User updated successfully"}), 200

# Admin: List/Create Subjects
@app.route('/api/admin/subjects', methods=['GET', 'POST'])
@admin_required
def admin_subjects():
    if request.method == 'GET':
        subjects = execute_query(
            """SELECT s.id, s.name, s.teacher_id, u.name as teacher_name
               FROM subjects s
               LEFT JOIN users u ON s.teacher_id = u.id
               ORDER BY s.name""",
            fetch='all'
        )
        return jsonify(subjects)

    elif request.method == 'POST':
        data = request.json
        name = data.get('name', '').strip()
        teacher_id = data.get('teacher_id')

        if not name or not teacher_id:
            return jsonify({"error": "Subject name and teacher are required"}), 400

        # Verify teacher exists
        teacher = execute_query("SELECT id FROM users WHERE id = %s AND role = 'teacher'", (int(teacher_id),), fetch='one')
        if not teacher:
            return jsonify({"error": "Invalid teacher selected"}), 400

        execute_query(
            "INSERT INTO subjects (name, teacher_id) VALUES (%s, %s)",
            (name, int(teacher_id))
        )
        return jsonify({"message": f"Subject '{name}' created successfully"}), 201

# Admin: Delete Subject
@app.route('/api/admin/subjects/<int:subject_id>', methods=['DELETE'])
@admin_required
def admin_subject_detail(subject_id):
    subject = execute_query("SELECT id FROM subjects WHERE id = %s", (subject_id,), fetch='one')
    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    # Cascade delete attendance, notes, assignments for this subject
    execute_query("DELETE FROM attendance WHERE subject_id = %s", (subject_id,))
    execute_query("DELETE FROM notes WHERE subject_id = %s", (subject_id,))
    execute_query("DELETE FROM assignments WHERE subject_id = %s", (subject_id,))
    execute_query("DELETE FROM subjects WHERE id = %s", (subject_id,))

    return jsonify({"message": "Subject deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
