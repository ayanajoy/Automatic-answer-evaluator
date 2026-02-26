import sqlite3
from datetime import datetime

# Create database connection
conn = sqlite3.connect("automatic_answer_checker.db", check_same_thread=False)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_answer TEXT NOT NULL,
    student_answer TEXT NOT NULL,
    similarity REAL NOT NULL,
    marks REAL NOT NULL,
    total_marks REAL NOT NULL,
    timestamp TEXT NOT NULL
)
""")

conn.commit()


def save_result(model_answer, student_answer, similarity, marks, total_marks):
    cursor.execute("""
    INSERT INTO results (model_answer, student_answer, similarity, marks, total_marks, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        model_answer,
        student_answer,
        similarity,
        marks,
        total_marks,
        datetime.utcnow().isoformat()
    ))

    conn.commit()


def get_all_results():
    cursor.execute("SELECT * FROM results ORDER BY id DESC")
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "model_answer": row[1],
            "student_answer": row[2],
            "similarity": row[3],
            "marks": row[4],
            "total_marks": row[5],
            "timestamp": row[6]
        })

    return results