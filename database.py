import sqlite3
from datetime import datetime

# Connect to SQLite
conn = sqlite3.connect("automatic_answer_checker.db", check_same_thread=False)
cursor = conn.cursor()

# Enable foreign key support
cursor.execute("PRAGMA foreign_keys = ON")


# ==================================================
# 1️⃣ QUESTION PAPERS TABLE
# ==================================================
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


# ==================================================
# 2️⃣ ANSWER SCHEME TABLE
# ==================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS answer_schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    answer_file_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES question_papers(id) ON DELETE CASCADE
)
""")


# ==================================================
# 3️⃣ STUDENTS TABLE
# ==================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TEXT NOT NULL
)
""")


# ==================================================
# 4️⃣ SUBMISSIONS TABLE
# ==================================================
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
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (paper_id) REFERENCES question_papers(id)
)
""")

conn.commit()


# ==================================================
# FUNCTION: ADD QUESTION PAPER
# ==================================================
def add_question_paper(subject_name, exam_title, total_marks, question_file_path):
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


def get_all_question_papers():
    cursor.execute("SELECT * FROM question_papers ORDER BY id DESC")
    return cursor.fetchall()


# ==================================================
# FUNCTION: ADD ANSWER SCHEME
# ==================================================
def add_answer_scheme(paper_id, answer_file_path):
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


def get_answer_scheme_by_paper(paper_id):
    cursor.execute("SELECT * FROM answer_schemes WHERE paper_id = ?", (paper_id,))
    return cursor.fetchone()


# ==================================================
# FUNCTION: ADD STUDENT
# ==================================================
def add_student(name, email):
    cursor.execute("""
    INSERT INTO students (name, email, created_at)
    VALUES (?, ?, ?)
    """, (
        name,
        email,
        datetime.utcnow().isoformat()
    ))
    conn.commit()


def get_all_students():
    cursor.execute("SELECT * FROM students")
    return cursor.fetchall()


# ==================================================
# FUNCTION: ADD SUBMISSION
# ==================================================
def add_submission(student_id, paper_id, question_number, student_answer, similarity, marks_awarded):
    cursor.execute("""
    INSERT INTO submissions
    (student_id, paper_id, question_number, student_answer, similarity, marks_awarded, submitted_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        paper_id,
        question_number,
        student_answer,
        similarity,
        marks_awarded,
        datetime.utcnow().isoformat()
    ))
    conn.commit()


def get_submissions_by_paper(paper_id):
    cursor.execute("""
    SELECT submissions.id,
           students.name,
           submissions.question_number,
           submissions.similarity,
           submissions.marks_awarded,
           submissions.submitted_at
    FROM submissions
    JOIN students ON submissions.student_id = students.id
    WHERE submissions.paper_id = ?
    ORDER BY submissions.submitted_at DESC
    """, (paper_id,))
    return cursor.fetchall()


def get_all_submissions():
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
    return cursor.fetchall()