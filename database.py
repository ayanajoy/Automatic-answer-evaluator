import sqlite3
from datetime import datetime
import os

DB_NAME = "automatic_answer_checker.db"


# ==================================================
# GET CONNECTION (Thread Safe)
# ==================================================
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==================================================
# CREATE TABLES (AUTO RUN)
# ==================================================
def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # USERS TABLE (AUTHENTICATION)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # QUESTION PAPERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL,
        exam_title TEXT NOT NULL,
        total_marks REAL NOT NULL,
        question_file_path TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # ANSWER SCHEMES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answer_schemes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        answer_file_path TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (paper_id) REFERENCES question_papers(id) ON DELETE CASCADE
    )
    """)

    # STUDENTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at TEXT NOT NULL
    )
    """)

    # SUBMISSIONS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        paper_id INTEGER NOT NULL,
        question_number INTEGER NOT NULL,
        student_answer TEXT NOT NULL,
        similarity REAL,
        marks_awarded REAL,
        submitted_at TEXT NOT NULL,
        submission_file TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (paper_id) REFERENCES question_papers(id) ON DELETE CASCADE
    )
    """)
    # ---------------------------------------
    # MIGRATION: Ensure submission_file exists
    # ---------------------------------------
    try:
        cursor.execute("ALTER TABLE submissions ADD COLUMN submission_file TEXT")
    except sqlite3.OperationalError:
        pass # Already exists

    conn.commit()
    conn.close()


# Call initialization when file loads
initialize_database()


# ==================================================
# QUESTION PAPER FUNCTIONS
# ==================================================
def add_question_paper(subject_name, exam_title, total_marks, question_file_path):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO question_papers
    (subject_name, exam_title, total_marks, question_file_path, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        subject_name,
        exam_title,
        total_marks,
        question_file_path,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def get_all_question_papers():
    conn = get_connection()
    cursor = conn.cursor()

    # Optimized to check for scheme existence in one go
    cursor.execute("""
    SELECT qp.*, (SELECT COUNT(*) FROM answer_schemes WHERE paper_id = qp.id) > 0 as has_scheme
    FROM question_papers qp
    ORDER BY qp.id DESC
    """)
    papers = cursor.fetchall()

    conn.close()
    return papers


# ==================================================
# ANSWER SCHEME FUNCTIONS
# ==================================================
def add_answer_scheme(paper_id, answer_file_path):
    conn = get_connection()
    cursor = conn.cursor()

    # 🔥 Delete old scheme for this paper
    cursor.execute(
        "DELETE FROM answer_schemes WHERE paper_id = ?",
        (paper_id,)
    )

    # Insert new scheme
    cursor.execute("""
    INSERT INTO answer_schemes
    (paper_id, answer_file_path, created_at)
    VALUES (?, ?, ?)
    """, (
        paper_id,
        answer_file_path,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def get_answer_scheme_by_paper(paper_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM answer_schemes
    WHERE paper_id = ?
    ORDER BY created_at DESC
    LIMIT 1
""", (paper_id,))
    scheme = cursor.fetchone()

    conn.close()
    return scheme


# ==================================================
# STUDENT FUNCTIONS
# ==================================================
def add_student(name, email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO students (name, email, created_at)
    VALUES (?, ?, ?)
    """, (
        name,
        email,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    conn.close()
    return students


# ==================================================
# SUBMISSION FUNCTIONS
# ==================================================
def add_submission(student_id, paper_id, question_number,
                   student_answer, similarity, marks_awarded, submission_file=None):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO submissions
    (student_id, paper_id, question_number,
     student_answer, similarity, marks_awarded, submitted_at, submission_file)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        paper_id,
        question_number,
        student_answer,
        similarity,
        marks_awarded,
        datetime.utcnow().isoformat(),
        submission_file
    ))

    conn.commit()
    conn.close()


def get_all_submissions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT submissions.id,
           students.name,
           question_papers.exam_title,
           submissions.question_number,
           submissions.similarity,
           submissions.marks_awarded,
           submissions.submitted_at
    FROM submissions
    JOIN students ON submissions.student_id = students.id
    JOIN question_papers ON submissions.paper_id = question_papers.id
    ORDER BY submissions.id DESC
    """)

    results = cursor.fetchall()
    conn.close()
    return results


# ==================================================
# DELETE PAPER FUNCTION
# ==================================================
def delete_question_paper(paper_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT question_file_path FROM question_papers WHERE id=?", (paper_id,))
    paper = cursor.fetchone()

    cursor.execute("SELECT answer_file_path FROM answer_schemes WHERE paper_id=?", (paper_id,))
    scheme = cursor.fetchone()

    cursor.execute("DELETE FROM question_papers WHERE id=?", (paper_id,))
    conn.commit()
    conn.close()

    if paper and paper[0] and os.path.exists(paper[0]):
        os.remove(paper[0])

    if scheme and scheme[0] and os.path.exists(scheme[0]):
        os.remove(scheme[0])

# ==================================================
# GET SUBMISSIONS BY PAPER (REQUIRED BY TEACHER ROUTES)
# ==================================================
def get_submissions_by_paper(paper_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT submissions.id,
           students.name,
           submissions.question_number,
           submissions.similarity,
           submissions.marks_awarded,
           submissions.submitted_at,
           question_papers.total_marks,
           submissions.student_answer,
           submissions.submission_file
    FROM submissions
    JOIN students ON submissions.student_id = students.id
    JOIN question_papers ON submissions.paper_id = question_papers.id
    WHERE submissions.paper_id = ?
    ORDER BY submissions.submitted_at DESC
    """, (paper_id,))

    results = cursor.fetchall()
    conn.close()
    return results

# ============================================
# GET STUDENT BY ID
# ============================================
def get_student_by_id(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()

    conn.close()
    return student

def register_user(name, email, password, role):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO users (name,email,password,role,created_at)
        VALUES (?,?,?,?,?)
        """, (
            name,
            email,
            password,
            role,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()
        return True

    except:
        conn.close()
        return False


def login_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id,name,role,email
    FROM users
    WHERE email=? AND password=?
    """, (email, password))

    user = cursor.fetchone()
    conn.close()

    return user

# ============================================
# GET STUDENT ANALYTICS
# ============================================
def get_student_analytics(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Aggregate the marks obtained and total possible marks per paper the student has submitted
    cursor.execute("""
    SELECT 
        question_papers.exam_title,
        question_papers.subject_name,
        question_papers.total_marks as max_marks,
        SUM(submissions.marks_awarded) as marks_obtained,
        MAX(submissions.submitted_at) as submission_date
    FROM submissions
    JOIN question_papers ON submissions.paper_id = question_papers.id
    WHERE submissions.student_id = ?
    GROUP BY submissions.paper_id, substr(submissions.submitted_at, 1, 16)
    ORDER BY submission_date ASC
    """, (student_id,))

    results = cursor.fetchall()
    conn.close()

    history = []
    for r in results:
        history.append({
            "exam_title": r[0],
            "subject": r[1],
            "max": float(r[2]),
            "obtained": float(r[3]),
            "percentage": round((float(r[3]) / float(r[2])) * 100, 2) if r[2] else 0,
            "date": r[4]
        })

    return history