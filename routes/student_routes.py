from fastapi import APIRouter, Form, UploadFile, File
import os
import shutil
import re

from database import (
    get_all_question_papers,
    add_submission,
    get_answer_scheme_by_paper
)

from nlp.similarity import calculate_similarity, calculate_marks

router = APIRouter(prefix="/student", tags=["Student"])

UPLOAD_FOLDER = "uploads/student_answers"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==============================
# 1️⃣ Get All Papers
# ==============================
@router.get("/papers")
def get_papers():
    return get_all_question_papers()


# ==============================
# 2️⃣ Get Paper Details
# ==============================
@router.get("/paper/{paper_id}")
def get_paper(paper_id: int):
    papers = get_all_question_papers()

    for paper in papers:
        if paper[0] == paper_id:
            return {
                "id": paper[0],
                "subject": paper[1],
                "exam_title": paper[2],
                "file_path": paper[4]
            }

    return {"error": "Paper not found"}


# ==============================
# 3️⃣ Extract Model Answer From TXT Scheme
# ==============================
def extract_model_answer(paper_id, question_number):

    scheme = get_answer_scheme_by_paper(paper_id)

    if not scheme:
        return None

    scheme_path = scheme[2]  # answer_file_path

    if not scheme_path.endswith(".txt"):
        return None

    with open(scheme_path, "r", encoding="utf-8") as file:
        content = file.read()

    pattern = rf"Q{question_number}:(.*?)(?=Q\d+:|$)"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1).strip()

    return None


# ==============================
# 4️⃣ Submit Answer
# ==============================
@router.post("/submit")
async def submit_answer(
    student_id: int = Form(...),
    paper_id: int = Form(...),
    question_number: int = Form(...),
    total_marks: float = Form(...),
    student_answer: str = Form(None),
    file: UploadFile = File(None)
):

    extracted_text = ""

    # If file uploaded
    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Placeholder OCR logic
        extracted_text = "Extracted text from uploaded file."

    if student_answer:
        extracted_text = student_answer

    if not extracted_text:
        return {"error": "No answer provided"}

    # 🔥 Get real model answer from answer scheme
    model_answer = extract_model_answer(paper_id, question_number)

    if not model_answer:
        return {"error": "Model answer not found for this question"}

    similarity = calculate_similarity(model_answer, extracted_text)
    marks = calculate_marks(similarity, total_marks)

    add_submission(
        student_id,
        paper_id,
        question_number,
        extracted_text,
        similarity,
        marks
    )

    return {
        "similarity": round(similarity, 4),
        "marks_awarded": marks
    }