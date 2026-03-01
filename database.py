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
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (paper_id) REFERENCES question_papers(id) ON DELETE CASCADE
    )
    """)

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

    cursor.execute("SELECT * FROM question_papers ORDER BY id DESC")
    papers = cursor.fetchall()

    conn.close()
    return papers


# ==================================================
# ANSWER SCHEME FUNCTIONS
# ==================================================
def add_answer_scheme(paper_id, answer_file_path):
    conn = get_connection()
    cursor = conn.cursor()

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

    cursor.execute("SELECT * FROM answer_schemes WHERE paper_id = ?", (paper_id,))
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
                   student_answer, similarity, marks_awarded):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO submissions
    (student_id, paper_id, question_number,
     student_answer, similarity, marks_awarded, submitted_at)
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
           submissions.submitted_at
    FROM submissions
    JOIN students ON submissions.student_id = students.id
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