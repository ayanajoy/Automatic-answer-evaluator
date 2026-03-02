from fastapi import APIRouter, Form, UploadFile, File
import json
import re
import pdfplumber
from docx import Document

from database import (
    get_all_question_papers,
    get_answer_scheme_by_paper,
    add_submission
)

from nlp.similarity import calculate_marks

router = APIRouter(prefix="/student", tags=["Student"])


# ============================================
# GET ALL PAPERS
# ============================================
@router.get("/papers")
def get_papers():
    return get_all_question_papers()


# ============================================
# GET QUESTIONS FROM ANSWER SCHEME
# ============================================
@router.get("/paper/{paper_id}/questions")
def get_questions(paper_id: int):

    scheme = get_answer_scheme_by_paper(paper_id)
    if not scheme:
        return {"error": "Answer scheme not found"}

    scheme_path = scheme[2]

    with open(scheme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"Q(\d+)\|(\d+):(.*?)(?=Q\d+\|\d+:|$)"
    matches = re.findall(pattern, content, re.DOTALL)

    questions = []
    for q_no, marks, _ in matches:
        questions.append({
            "question_number": int(q_no),
            "marks": int(marks)
        })

    return questions


# ============================================
# SUBMIT FULL PAPER (Typed OR File Upload)
# ============================================
@router.post("/submit-paper")
async def submit_paper(
    student_id: int = Form(...),
    paper_id: int = Form(...),
    answers: str = Form(None),
    file: UploadFile = File(None)
):

    # ---------------------------------------
    # VALIDATE PAPER
    # ---------------------------------------
    papers = get_all_question_papers()
    paper_ids = [p[0] for p in papers]

    if paper_id not in paper_ids:
        return {"error": "Invalid paper selected."}

    # ---------------------------------------
    # AUTO CREATE STUDENT IF NOT EXISTS
    # ---------------------------------------
    from database import get_student_by_id, add_student

    student = get_student_by_id(student_id)

    if not student:
        add_student(
            f"Student {student_id}",
            f"student{student_id}@mail.com"
        )

    # ---------------------------------------
    # LOAD ANSWER SCHEME
    # ---------------------------------------
    scheme = get_answer_scheme_by_paper(paper_id)
    if not scheme:
        return {"error": "Answer scheme not found"}

    scheme_path = scheme[2]

    with open(scheme_path, "r", encoding="utf-8") as f:
        scheme_content = f.read()

    pattern = r"Q(\d+)\|(\d+):(.*?)(?=Q\d+\|\d+:|$)"
    matches = re.findall(pattern, scheme_content, re.DOTALL)

    student_answers = {}

    # ---------------------------------------
    # CASE 1: Typed Answers
    # ---------------------------------------
    if answers:
        student_answers = json.loads(answers)

    # ---------------------------------------
    # CASE 2: File Upload
    # ---------------------------------------
    elif file:

        extracted_text = ""

        from io import BytesIO

        file_content = await file.read()

        # PDF
        if file.filename.endswith(".pdf"):
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"

        # DOCX
        elif file.filename.endswith(".docx"):
            doc = Document(BytesIO(file_content))
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"

        else:
            return {"error": "Unsupported file type."}

        split_pattern = r"Q(\d+):(.*?)(?=Q\d+:|$)"
        found_answers = re.findall(split_pattern, extracted_text, re.DOTALL)

        for q_no, ans in found_answers:
            student_answers[q_no] = ans.strip()

    else:
        return {"error": "No answers provided."}

    # ---------------------------------------
    # EVALUATE PAPER
    # ---------------------------------------
    total_marks = 0
    total_obtained = 0
    detailed_results = []

    for q_no, marks, model_answer in matches:

        q_no = int(q_no)
        marks = int(marks)
        total_marks += marks

        student_answer = student_answers.get(str(q_no), "")

        # ✅ Hybrid scoring
        obtained, breakdown = calculate_marks(
            model_answer.strip(),
            student_answer,
            marks
        )

        total_obtained += obtained

        detailed_results.append({
            "question": q_no,
            "marks_awarded": obtained,
            "max_marks": marks,
            "semantic_score": breakdown["semantic"],
            "keyword_score": breakdown["keyword"],
            "length_score": breakdown["length"]
        })

        add_submission(
            student_id,
            paper_id,
            q_no,
            student_answer,
            breakdown["semantic"],   # store semantic similarity
            obtained
        )

    return {
        "total_marks": total_marks,
        "total_obtained": total_obtained,
        "details": detailed_results
    }