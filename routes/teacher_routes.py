from fastapi import APIRouter, UploadFile, File, Form
import shutil
import os
from database import delete_question_paper
from database import (
    add_question_paper,
    get_all_question_papers,
    add_answer_scheme,
    get_all_submissions,
    get_submissions_by_paper
)

router = APIRouter(prefix="/teacher", tags=["Teacher"])


# ==============================
# Create Upload Folders
# ==============================
QUESTION_FOLDER = "uploads/question_papers"
ANSWER_FOLDER = "uploads/answer_schemes"

os.makedirs(QUESTION_FOLDER, exist_ok=True)
os.makedirs(ANSWER_FOLDER, exist_ok=True)


# ==============================
# 1️⃣ Upload Question Paper
# ==============================
@router.post("/upload-paper")
async def upload_question_paper(
    subject_name: str = Form(...),
    exam_title: str = Form(...),
    total_marks: float = Form(...),
    file: UploadFile = File(...)
):

    file_path = os.path.join(QUESTION_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    add_question_paper(
        subject_name,
        exam_title,
        total_marks,
        file_path
    )

    return {"message": "Question paper uploaded successfully"}


# ==============================
# 2️⃣ Upload Answer Scheme
# ==============================
@router.post("/upload-scheme")
async def upload_answer_scheme(
    paper_id: int = Form(...),
    file: UploadFile = File(...)
):

    file_path = os.path.join(ANSWER_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    add_answer_scheme(paper_id, file_path)

    return {"message": "Answer scheme uploaded successfully"}


# ==============================
# 3️⃣ Get All Question Papers
# ==============================
@router.get("/papers")
def get_papers():
    papers = get_all_question_papers()
    return papers


# ==============================
# 4️⃣ Get Submissions for Paper
# ==============================
@router.get("/submissions/{paper_id}")
def get_submissions(paper_id: int):
    submissions = get_submissions_by_paper(paper_id)
    return submissions


# ==============================
# 5️⃣ Get All Submissions
# ==============================
@router.get("/all-submissions")
def get_all():
    return get_all_submissions()

@router.delete("/delete-paper/{paper_id}")
def delete_paper(paper_id: int):
    delete_question_paper(paper_id)
    return {"message": "Paper deleted successfully"}

@router.get("/scheme/{paper_id}")
def get_scheme(paper_id: int):
    from database import get_answer_scheme_by_paper
    scheme = get_answer_scheme_by_paper(paper_id)

    if not scheme:
        return {"error": "No scheme found"}

    return {
        "file_path": scheme[2]
    }

@router.get("/analytics/{paper_id}")
def get_paper_analytics(paper_id: int):
    submissions = get_submissions_by_paper(paper_id)
    if not submissions:
        return {"error": "No submissions yet"}
    
    # Paper total marks (index 6 in get_submissions_by_paper)
    paper_total = submissions[0][6]
    
    # sessions index 1 is student name, 5 is timestamp, 4 is marks_awarded
    sessions = {}
    for s in submissions:
        # Use second-level granularity for legacy data
        ts = s[5] if s[5] else ""
        session_key = (s[1], ts[:19]) # (Name, Timestamp to second)
        
        if session_key not in sessions:
            sessions[session_key] = 0
        sessions[session_key] += float(s[4] or 0)
        
    student_totals = list(sessions.values())
    
    if not student_totals:
        return {"error": "No valid scores found"}

    avg_score = sum(student_totals) / len(student_totals)
    highest_score = max(student_totals)
    
    return {
        "average": round(avg_score, 2),
        "highest": round(highest_score, 2),
        "total_students": len(set(s[1] for s in submissions)),
        "total_submissions": len(student_totals),
        "pass_rate": round((len([s for s in student_totals if (s / paper_total) >= 0.4]) / len(student_totals)) * 100, 1) if paper_total else 0,
        "scores": student_totals,
        "max_marks": paper_total
    }