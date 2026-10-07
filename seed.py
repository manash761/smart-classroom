from werkzeug.security import generate_password_hash
from database import execute_query, init_db, get_db_connection
import datetime

DEPARTMENTS = [
    "Computer Science Department",
    "Electrical Department",
    "Printing Technology",
]

def seed_data():
    # Make sure tables exist
    init_db()

    print("Seeding database...")

    # 0. Seed Admin Account
    admin_user = execute_query("SELECT id FROM users WHERE username = %s AND role = %s", ("admin", "admin"), fetch='one')
    if not admin_user:
        execute_query(
            "INSERT INTO users (username, password_hash, role, name, roll_number) VALUES (%s, %s, %s, %s, NULL)",
            ("admin", generate_password_hash("admin@123"), "admin", "System Administrator")
        )
        print("Admin account created: username 'admin', password 'admin@123'")
    else:
        print("Admin account already exists.")

    # 1. Seed Teachers
    teachers_data = [
        ("teacher", "RAMEN KR CHOUDHURY", "admin123"),
        ("teacher2", "KANGKA CHAKRAVARTY", "admin456"),
        ("teacher3", "NARZITORA ALOM", "admin456"),
        ("teacher4", "Doli CHAKRAVARTY", "admin456"),
        ("teacher5", "HEMANTA KUMAR PATHAK", "admin456"),
    ]

    teacher_ids = {}
    for username, name, password in teachers_data:
        teacher = execute_query("SELECT id FROM users WHERE username = %s", (username,), fetch='one')
        if not teacher:
            t_id = execute_query(
                "INSERT INTO users (username, password_hash, role, name, roll_number) VALUES (%s, %s, %s, %s, NULL)",
                (username, generate_password_hash(password), "teacher", name)
            )
            if not t_id:
                t_id = execute_query("SELECT id FROM users WHERE username = %s", (username,), fetch='one')['id']
            print(f"Teacher account created: username '{username}', password '{password}', ID {t_id}")
            teacher_ids[username] = t_id
        else:
            t_id = teacher['id']
            teacher_ids[username] = t_id
            print(f"Teacher account already exists: {name} (username: '{username}')")

    # Use first teacher as default fallback
    teacher_id = teacher_ids.get('teacher')

    # 2. Seed Students
    students_data = [
        ("2301876", "abdulrazak", "Abdul Razak", "password123"),
        ("2301877", "ankurdeka", "Ankur Deka", "password123"),
        ("2301878", "bhardwaj", "Bhardwaj Bhargav Sakia", "password123"),
        ("2301879", "bishwaranjan", "Bishwaranjan Deori", "password123"),
        ("2301880", "dhanmani", "Dhanmani Bhuyan", "password123"),
        ("2301882", "dikshit", "Dikshit Choudhury", "password123"),
        ("2301883", "dikshita", "Dikshita Kashyap", "password123"),
        ("2301884", "dipsikha", "Dipsikha Borgohain", "password123"),
        ("2301885", "faruk", "Faruk Abdula", "password123"),
        ("2301886", "gunjan", "Gunjan Boro", "password123"),
        ("2301887", "hemanta", "Hemanta Boro", "password123"),
        ("2301888", "hirakjyoti", "Hirakjyoti Kalita", "password123"),
        ("2301891", "jayashri", "Jayashri Hazoi", "password123"),
        ("2301892", "jibanjyoti", "Jibanjyoti Hujuri", "password123"),
        ("2301893", "jugal", "Jugal Barua", "password123"),
        ("2301894", "junmoni", "Junmoni Baro", "password123"),
        ("2301895", "kakuli", "Kakuli Das", "password123"),
        ("2301896", "kalyan", "Kalyan Jyoti Sonowal", "password123"),
        ("2301898", "koushik", "Koushik Kumar Borah", "password123"),
        ("2301899", "madhusmita", "Madhusmita Deka", "password123"),
        ("2301900", "manash", "Manash Jyoti Phukon", "password123"),
        ("2301901", "monish", "Monish Bhuel", "password123"),
        ("2301902", "mrinal", "Mrinal Rava", "password123"),
        ("2301903", "nishan", "Nishan Biswas", "password123"),
        ("2301904", "nitish", "Nitish Gogoi", "password123"),
        ("2301905", "pinakhi", "Pinakhi Barman", "password123"),
        ("2301906", "pritam", "Pritam Pathak", "password123"),
        ("2301907", "priyanchi", "Priyanchi Dutta", "password123"),
        ("2301908", "raman", "Raman Das Kalita", "password123"),
        ("2301909", "rashida", "Rashida Khatun", "password123"),
        ("2301911", "rikic", "Riki Changmai ", "password123"),
        ("2301912", "riki", "Riki Kalita", "password123"),
        ("2301913", "rituparna", "Ritu Parna Choudhury", "password123"),
        ("2301914", "rituraj", "Rituraj Ray", "password123"),
        ("2301915", "riturajthakuria", "Rituraj Thakuria", "password123"),
        ("2301916", "riya", "Riya Kumari", "password123"),
        ("2301917", "robert", "Robert Gogoi", "password123"),
        ("2301918", "shanjit", "Shanjit Biswas", "password123"),
        ("2301920", "simanta", "Simanta Baishya", "password123"),
        ("2301921", "simantap", "Simanta Pathak", "password123"),
        ("2301922", "udangshi", "Udangshi Baro", "password123"),
        ("2301923", "uddipta", "Uddipta Roy", "password123"),
        ("NA/21/CO/073", "pradyumna", "Pradyumna Kashyap", "password123")
    ]

    student_ids = []
    for roll, username, name, password in students_data:
        student_index = len(student_ids)
        semester = (student_index % 6) + 1
        department = DEPARTMENTS[student_index % len(DEPARTMENTS)]
        student = execute_query("SELECT id FROM users WHERE username = %s", (username,), fetch='one')
        if not student:
            s_id = execute_query(
                """INSERT INTO users (username, password_hash, role, name, roll_number, semester, department)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (username, generate_password_hash(password), "student", name, roll, semester, department)
            )
            if not s_id:
                s_id = execute_query("SELECT id FROM users WHERE username = %s", (username,), fetch='one')['id']
            print(f"Student created: {name} (Roll: {roll}, username: '{username}')")
            student_ids.append(s_id)
        else:
            execute_query(
                """UPDATE users
                   SET semester = COALESCE(semester, %s),
                       department = COALESCE(department, %s)
                   WHERE id = %s""",
                (semester, department, student['id'])
            )
            student_ids.append(student['id'])
            print(f"Student already exists: {name} (Roll: {roll})")

    # 3. Seed Subjects
    subjects_data = [
        ("Database Management Systems", teacher_ids.get('teacher')),
        ("Web Technologies", teacher_ids.get('teacher')),
        ("Software Engineering", teacher_ids.get('teacher2'))
    ]
    
    subject_map = {}
    for name, t_id in subjects_data:
        sub = execute_query("SELECT id FROM subjects WHERE name = %s", (name,), fetch='one')
        if not sub:
            s_id = execute_query(
                "INSERT INTO subjects (name, teacher_id) VALUES (%s, %s)",
                (name, t_id)
            )
            if not s_id:
                s_id = execute_query("SELECT id FROM subjects WHERE name = %s", (name,), fetch='one')['id']
            print(f"Subject created: '{name}' (Teacher ID: {t_id})")
            subject_map[name] = s_id
        else:
            s_id = sub['id']
            subject_map[name] = s_id
            print(f"Subject already exists: '{name}' (ID: {s_id})")

    # 4. Seed Notices
    notices_data = [
        ("Welcome to Smart Classroom", "Welcome to the new semester! This system will be used for daily attendance tracking, notes, resources, and assignment submissions. Ensure you review the guidelines.", teacher_id),
        ("Mid-Term Examinations", "Mid-term exams will commence from next week. Please verify your attendance percentage; a minimum of 75% attendance is required to sit for the exams.", teacher_id)
    ]
    for title, content, uploaded_by in notices_data:
        existing = execute_query("SELECT id FROM notices WHERE title = %s", (title,), fetch='one')
        if not existing:
            execute_query(
                "INSERT INTO notices (title, content, uploaded_by) VALUES (%s, %s, %s)",
                (title, content, uploaded_by)
            )
            print(f"Notice created: '{title}'")

    # 5. Seed Notes/Resources with subject_id
    notes_data = [
        ("Lecture 1: Database System Concepts", "Introduction to database systems, relational database models, schemas, and queries.", "lecture1_db_concepts.pdf", "static/uploads/notes/lecture1_db_concepts.pdf", teacher_ids.get('teacher'), subject_map.get("Database Management Systems")),
        ("Lecture 1: Web Client-Server", "Understanding client-server models, HTTP protocols, HTML, and browser rendering.", "lecture1_web_intro.pdf", "static/uploads/notes/lecture1_web_intro.pdf", teacher_ids.get('teacher'), subject_map.get("Web Technologies")),
        ("Lecture 1: Software Lifecycle Models", "Introduction to software engineering principles, SDLC models, and Agile methodologies.", "lecture1_software_lifecycle.pdf", "static/uploads/notes/lecture1_software_lifecycle.pdf", teacher_ids.get('teacher2'), subject_map.get("Software Engineering"))
    ]
    for title, description, file_name, file_path, uploaded_by, sub_id in notes_data:
        existing = execute_query("SELECT id FROM notes WHERE title = %s", (title,), fetch='one')
        if not existing:
            execute_query(
                "INSERT INTO notes (title, description, file_name, file_path, uploaded_by, subject_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (title, description, file_name, file_path, uploaded_by, sub_id)
            )
            print(f"Note created: '{title}'")

    # 6. Seed Assignments with subject_id
    today = datetime.date.today()
    assignments_data = [
        ("Assignment 1: ER Diagram Design", "Design a relational ER Diagram for a library database system.", today + datetime.timedelta(days=7), teacher_ids.get('teacher'), subject_map.get("Database Management Systems")),
        ("Assignment 1: CSS Grid & Flexbox", "Create a responsive webpage layout using only HTML and vanilla CSS grid/flexbox styles.", today + datetime.timedelta(days=10), teacher_ids.get('teacher'), subject_map.get("Web Technologies")),
        ("Assignment 1: Software Requirements Spec", "Write a complete SRS document for the Smart Classroom System project.", today + datetime.timedelta(days=14), teacher_ids.get('teacher2'), subject_map.get("Software Engineering"))
    ]
    for title, description, due_date, uploaded_by, sub_id in assignments_data:
        existing = execute_query("SELECT id FROM assignments WHERE title = %s", (title,), fetch='one')
        if not existing:
            execute_query(
                "INSERT INTO assignments (title, description, due_date, uploaded_by, subject_id) VALUES (%s, %s, %s, %s, %s)",
                (title, description, due_date, uploaded_by, sub_id)
            )
            print(f"Assignment created: '{title}'")

    # 7. Seed Attendance records for past 3 days for EACH subject
    for i in range(1, 4):
        past_date = today - datetime.timedelta(days=i)
        if past_date.weekday() >= 5: # Skip weekends
            continue
        
        # Seed statuses deterministically per subject
        for sub_name, sub_id in subject_map.items():
            for s_idx, s_id in enumerate(student_ids):
                if sub_name == "Database Management Systems":
                    status = "Present" if s_idx % 2 == 0 else ("Late" if s_idx % 5 == 1 else "Absent")
                elif sub_name == "Web Technologies":
                    status = "Present" if s_idx % 3 != 2 else "Absent"
                else:
                    status = "Present" if s_idx % 7 != 4 else "Late"
                
                # Check if record already exists
                existing = execute_query(
                    "SELECT id FROM attendance WHERE student_id = %s AND subject_id = %s AND attendance_date = %s",
                    (s_id, sub_id, past_date), fetch='one'
                )
                if not existing:
                    execute_query(
                        "INSERT INTO attendance (student_id, subject_id, attendance_date, status) VALUES (%s, %s, %s, %s)",
                        (s_id, sub_id, past_date, status)
                    )
    print("Attendance records for past 3 days seeded.")
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed_data()
