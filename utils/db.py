"""
Database utility module.
Handles SQLite connection, schema creation, and query helpers.
SQL injection protection via parameterized queries throughout.
"""

import sqlite3
import bcrypt
from config import Config


def get_db():
    """Return a new SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize the database schema and insert default admin."""
    conn = get_db()
    cursor = conn.cursor()

    # --- Admins table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role        TEXT DEFAULT 'admin',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Students table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            department  TEXT NOT NULL,
            semester    TEXT NOT NULL,
            email       TEXT,
            phone       TEXT,
            image_path  TEXT,
            face_trained INTEGER DEFAULT 0,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Attendance table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id    TEXT NOT NULL,
            student_name  TEXT NOT NULL,
            department    TEXT,
            date          TEXT NOT NULL,
            time          TEXT NOT NULL,
            confidence    REAL DEFAULT 0.0,
            status        TEXT DEFAULT 'Present',
            UNIQUE(student_id, date),
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )
    """)

    # Insert default admin if not exists
    existing = cursor.execute(
        "SELECT id FROM admins WHERE username = ?", (Config.ADMIN_USERNAME,)
    ).fetchone()

    if not existing:
        hashed = bcrypt.hashpw(Config.ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO admins (username, password_hash, role) VALUES (?, ?, ?)",
            (Config.ADMIN_USERNAME, hashed, 'admin')
        )

    conn.commit()
    conn.close()


def verify_admin(username, password):
    """Verify admin credentials. Returns admin dict or None."""
    conn = get_db()
    admin = conn.execute(
        "SELECT * FROM admins WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if admin and bcrypt.checkpw(password.encode(), admin['password_hash'].encode()):
        return dict(admin)
    return None


# -------- Student helpers --------

def get_all_students():
    conn = get_db()
    rows = conn.execute("SELECT * FROM students ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_by_id(student_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM students WHERE student_id = ?", (student_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_student_by_pk(pk):
    conn = get_db()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (pk,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_student(student_id, name, department, semester, email, phone, image_path=''):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO students (student_id, name, department, semester, email, phone, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, name, department, semester, email, phone, image_path))
        conn.commit()
        return True, "Student added successfully"
    except sqlite3.IntegrityError:
        return False, "Student ID already exists"
    finally:
        conn.close()


def update_student(pk, name, department, semester, email, phone):
    conn = get_db()
    conn.execute("""
        UPDATE students SET name=?, department=?, semester=?, email=?, phone=?
        WHERE id=?
    """, (name, department, semester, email, phone, pk))
    conn.commit()
    conn.close()


def delete_student(pk):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (pk,))
    conn.commit()
    conn.close()


def mark_student_trained(student_id):
    conn = get_db()
    conn.execute(
        "UPDATE students SET face_trained=1 WHERE student_id=?", (student_id,)
    )
    conn.commit()
    conn.close()


def get_students_count():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()
    return count


def get_trained_students():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM students WHERE face_trained=1"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# -------- Attendance helpers --------

def mark_attendance(student_id, student_name, department, confidence):
    """Mark attendance once per day. Returns (success, message)."""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M:%S')
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO attendance (student_id, student_name, department, date, time, confidence, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Present')
        """, (student_id, student_name, department, today, now_time, round(confidence, 4)))
        conn.commit()
        return True, f"Attendance marked for {student_name}"
    except sqlite3.IntegrityError:
        return False, f"Already marked for {student_name} today"
    finally:
        conn.close()


def get_attendance(date_filter=None, student_filter=None, dept_filter=None):
    conn = get_db()
    query = "SELECT * FROM attendance WHERE 1=1"
    params = []
    if date_filter:
        query += " AND date = ?"
        params.append(date_filter)
    if student_filter:
        query += " AND (student_id LIKE ? OR student_name LIKE ?)"
        params.extend([f'%{student_filter}%', f'%{student_filter}%'])
    if dept_filter and dept_filter != 'All':
        query += " AND department = ?"
        params.append(dept_filter)
    query += " ORDER BY date DESC, time DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_attendance_count():
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=?", (today,)
    ).fetchone()[0]
    conn.close()
    return count


def get_attendance_stats():
    """Return stats for dashboard."""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    present_today = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=?", (today,)
    ).fetchone()[0]
    
    # Monthly data for chart
    monthly = conn.execute("""
        SELECT date, COUNT(*) as count 
        FROM attendance 
        WHERE date >= date('now', '-30 days')
        GROUP BY date 
        ORDER BY date
    """).fetchall()
    
    # Department-wise attendance today
    dept_stats = conn.execute("""
        SELECT department, COUNT(*) as count
        FROM attendance
        WHERE date=?
        GROUP BY department
    """, (today,)).fetchall()
    
    conn.close()
    
    attendance_pct = round((present_today / total_students * 100), 1) if total_students > 0 else 0
    
    return {
        'total_students': total_students,
        'present_today': present_today,
        'attendance_pct': attendance_pct,
        'monthly': [{'date': r['date'], 'count': r['count']} for r in monthly],
        'dept_stats': [{'dept': r['department'], 'count': r['count']} for r in dept_stats],
    }


def get_departments():
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT department FROM students ORDER BY department").fetchall()
    conn.close()
    return [r['department'] for r in rows]
