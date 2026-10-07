import os
import sqlite3
import urllib.parse

# Determine database type
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_POSTGRES = DATABASE_URL is not None

def get_db_connection():
    """Returns a connection to the database. Uses PostgreSQL if DATABASE_URL is set, otherwise SQLite."""
    if IS_POSTGRES:
        import psycopg2
        import psycopg2.extras
        # Parse connection string to handle sslmode for cloud providers like Neon/Render
        url = urllib.parse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            sslmode='require' # Neon and Render require SSL
        )
        return conn
    else:
        # SQLite
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'classroom.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=OFF")
        return conn

def execute_query(query, params=None, fetch='none'):
    """
    Executes a query and automatically handles parameter placeholder differences.
    - query: SQL query string using '%s' as placeholders.
    - params: tuple or list of parameters.
    - fetch: 'none', 'one', or 'all'.
    """
    if params is None:
        params = ()

    conn = get_db_connection()
    cursor = None
    result = None

    try:
        if IS_POSTGRES:
            import psycopg2.extras
            # Use DictCursor to mimic sqlite3.Row (access by column name)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(query, params)
        else:
            cursor = conn.cursor()
            # SQLite uses '?' instead of '%s'
            sqlite_query = query.replace('%s', '?')
            cursor.execute(sqlite_query, params)

        if fetch == 'one':
            row = cursor.fetchone()
            # Convert to dict for uniform access
            result = dict(row) if row else None
        elif fetch == 'all':
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
        else:
            conn.commit()
            result = cursor.lastrowid if not IS_POSTGRES else None
            
        if fetch == 'none':
            conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        conn.close()

    return result

def column_exists(table_name, column_name):
    """Checks whether a column exists on the active database."""
    conn = get_db_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        if IS_POSTGRES:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
                """,
                (table_name, column_name)
            )
            return cursor.fetchone() is not None

        cursor.execute(f"PRAGMA table_info({table_name})")
        return any(row[1] == column_name for row in cursor.fetchall())
    finally:
        if cursor:
            cursor.close()
        conn.close()

def add_column_if_missing(table_name, column_name, column_definition):
    """Adds a column for older local databases without rebuilding tables."""
    if not column_exists(table_name, column_name):
        execute_query(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

def init_db():
    """Initializes database tables."""
    # Build schema. Note differences in primary key autoincrement
    serial_type = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    text_type = "VARCHAR(255)" if IS_POSTGRES else "TEXT"
    long_text_type = "TEXT"
    
    # Create Users table
    execute_query(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {serial_type},
            username {text_type} UNIQUE NOT NULL,
            password_hash {text_type} NOT NULL,
            role {text_type} NOT NULL, -- 'teacher' or 'student'
            name {text_type} NOT NULL,
            roll_number {text_type} UNIQUE, -- Null for teachers
            semester INTEGER,
            department {text_type}
        )
    """)
    add_column_if_missing('users', 'semester', 'INTEGER')
    add_column_if_missing('users', 'department', text_type)

    # Create Subjects table
    execute_query(f"""
        CREATE TABLE IF NOT EXISTS subjects (
            id {serial_type},
            name {text_type} NOT NULL,
            teacher_id INTEGER NOT NULL
        )
    """)

    # Create Attendance table with subject_id and updated UNIQUE constraint
    execute_query(f"""
        CREATE TABLE IF NOT EXISTS attendance (
            id {serial_type},
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status {text_type} NOT NULL, -- 'Present', 'Absent', 'Late'
            UNIQUE (student_id, subject_id, attendance_date)
        )
    """)

    # Create Notes table with subject_id
    execute_query(f"""
        CREATE TABLE IF NOT EXISTS notes (
            id {serial_type},
            title {text_type} NOT NULL,
            description {long_text_type},
            file_name {text_type}, -- Original name of uploaded file
            file_path {text_type}, -- Local path or URL
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER NOT NULL,
            subject_id INTEGER NOT NULL
        )
    """)

    # Create Assignments table with subject_id
    execute_query(f"""
        CREATE TABLE IF NOT EXISTS assignments (
            id {serial_type},
            title {text_type} NOT NULL,
            description {long_text_type},
            due_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER NOT NULL,
            subject_id INTEGER NOT NULL
        )
    """)

    # Create Notices table
    execute_query(f"""
        CREATE TABLE IF NOT EXISTS notices (
            id {serial_type},
            title {text_type} NOT NULL,
            content {long_text_type} NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER NOT NULL
        )
    """)
    print("Database tables initialized successfully.")

if __name__ == '__main__':
    init_db()
