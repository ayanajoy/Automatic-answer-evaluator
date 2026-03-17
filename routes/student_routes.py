import json
import re
import os
import shutil
import pdfplumber
from docx import Document

from database import (
    get_all_question_papers,
    get_answer_scheme_by_paper,
    add_submission,
    get_student_analytics
)

from nlp.similarity import calculate_marks, generate_explanation

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

    with open(scheme_path, "r", encoding="utf-8", errors="ignore") as f:
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
# SUBMIT PAPER
# ============================================
@router.post("/submit-paper")
async def submit_paper(
    student_id: int = Form(...),
    paper_id: int = Form(...),
    answers: str = Form(None),
    file: UploadFile = File(None)
):
    # Setup permanent storage
    STUDENT_SUBMISSION_FOLDER = "uploads/student_submissions"
    os.makedirs(STUDENT_SUBMISSION_FOLDER, exist_ok=True)
    stored_file_path = None

    # ---------------------------------------
    # VALIDATE PAPER
    # ---------------------------------------
    papers = get_all_question_papers()
    paper_ids = [p[0] for p in papers]

    if paper_id not in paper_ids:
        return {"error": "Invalid paper selected."}

    # ---------------------------------------
    # AUTO CREATE STUDENT
    # ---------------------------------------
    from database import get_student_by_id, get_connection
    from datetime import datetime

    student = get_student_by_id(student_id)

    if not student:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO students (id, name, email, created_at)
            VALUES (?, ?, ?, ?)
            """, (student_id, f"Student {student_id}", f"student{student_id}@mail.com", datetime.utcnow().isoformat()))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    # ---------------------------------------
    # LOAD ANSWER SCHEME
    # ---------------------------------------
    scheme = get_answer_scheme_by_paper(paper_id)
    if not scheme:
        return {"error": "Answer scheme not found"}

    scheme_path = scheme[2]

    with open(scheme_path, "r", encoding="utf-8", errors="ignore") as f:
        scheme_content = f.read()

    pattern = r"Q(\d+)\|(\d+):(.*?)(?=Q\d+\|\d+:|$)"
    matches = re.findall(pattern, scheme_content, re.DOTALL)

    student_answers = {}

    # ---------------------------------------
    # CASE 1: TYPED ANSWERS
    # ---------------------------------------
    if answers:
        student_answers = json.loads(answers)

    # ---------------------------------------
    # CASE 2: FILE UPLOAD
    # ---------------------------------------
    elif file:

        extracted_text = ""

        from io import BytesIO
        file_content = await file.read()

        # PDF → OCR
        if file.filename.endswith(".pdf"):

            import tempfile
            from ocr import extract_text_from_pdf

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                temp.write(file_content)
                temp_path = temp.name

            extracted_text = extract_text_from_pdf(temp_path)

        # DOCX
        elif file.filename.endswith(".docx"):
            doc = Document(BytesIO(file_content))
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"

        else:
            return {"error": "Unsupported file type."}

        # Save the file permanently
        stored_file_path = os.path.join(STUDENT_SUBMISSION_FOLDER, f"S{student_id}_P{paper_id}_{file.filename}")
        with open(stored_file_path, "wb") as buffer:
            buffer.write(file_content)

        # ---------------------------------------
        # DEBUG: SHOW OCR TEXT
        # ---------------------------------------
        print("\n================ OCR OUTPUT ================")
        print(extracted_text)
        print("============================================\n")

        # Fix common OCR mistakes
        extracted_text = extracted_text.replace("Ql", "Q1")
        extracted_text = extracted_text.replace("QI", "Q1")
        extracted_text = extracted_text.replace("Qi", "Q1")
        extracted_text = extracted_text.replace("Q l", "Q1")
        extracted_text = extracted_text.replace("Q I", "Q1")

        # ---------------------------------------
        # OCR FRIENDLY QUESTION SPLIT
        # ---------------------------------------
        split_pattern = r"(?:^|\n)\s*(?:Q|Question|Ans|Answer|Q\s*)?\.?\s*([0-9]+)[\:\.\-\)]\s*(.*?)(?=(?:^|\n)\s*(?:Q|Question|Ans|Answer|Q\s*)?\.?\s*[0-9]+[\:\.\-\)]|$)"

        found_answers = re.findall(split_pattern, extracted_text, re.DOTALL | re.IGNORECASE)

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

    # If OCR text exists but answers weren't found via regex, we prepare for semantic search
    from nlp.similarity import model as emb_model
    from sklearn.metrics.pairwise import cosine_similarity
    
    ocr_sentences = []
    ocr_embeddings = []
    
    if file and extracted_text:
        import nltk
        ocr_sentences = nltk.sent_tokenize(extracted_text)
        if ocr_sentences:
            ocr_embeddings = emb_model.encode(ocr_sentences)

    for q_no, marks, model_answer in matches:

        q_no = int(q_no)
        marks = int(marks)
        total_marks += marks

        student_answer = student_answers.get(str(q_no), "")
        
        # ---------------------------------------
        # FALLBACK: SEMANTIC SEARCH
        # If student answer is empty but we have OCR text
        # ---------------------------------------
        if not student_answer.strip() and ocr_embeddings is not None and len(ocr_embeddings) > 0:
            best_chunk = ""
            best_sim = 0
            
            model_emb = emb_model.encode([model_answer])
            
            # Use a slightly larger window context (combine current sentence with next)
            for i in range(len(ocr_sentences)):
                window_text = ocr_sentences[i]
                if i + 1 < len(ocr_sentences):
                    window_text += " " + ocr_sentences[i+1]
                if i + 2 < len(ocr_sentences):
                    window_text += " " + ocr_sentences[i+2]
                    
                window_emb = emb_model.encode([window_text])
                sim = cosine_similarity(model_emb, window_emb)[0][0]
                
                if sim > best_sim:
                    best_sim = sim
                    best_chunk = window_text
            
            # If the best chunk has reasonable relevance, assume it's the answer
            if best_sim > 0.3:
                student_answer = best_chunk
                print(f"Fallback matched Q{q_no} with similarity {best_sim:.2f}")

        obtained, breakdown = calculate_marks(
            model_answer.strip(),
            student_answer,
            marks
        )

        explanation = generate_explanation(breakdown)

        total_obtained += float(obtained)

        detailed_results.append({
            "question": int(q_no),
            "marks_awarded": float(obtained),
            "max_marks": int(marks),
            "semantic_score": float(breakdown["semantic"]),
            "keyword_score": float(breakdown["keyword"]),
            "length_score": float(breakdown["length"]),
            "concept_coverage": breakdown["concept_coverage"],
            "explanation": explanation
        })

        add_submission(
            student_id,
            paper_id,
            q_no,
            student_answer,
            float(breakdown["semantic"]),
            float(obtained),
            stored_file_path
        )

    return {
        "total_marks": int(total_marks),
        "total_obtained": float(total_obtained),
        "details": detailed_results
    }


# ============================================
# GET PAPER DETAILS
# ============================================
@router.get("/paper/{paper_id}")
def get_paper_details(paper_id: int):

    papers = get_all_question_papers()

    for paper in papers:
        if paper[0] == paper_id:

            scheme = get_answer_scheme_by_paper(paper_id)

            return {
                "id": paper[0],
                "subject": paper[1],
                "exam_title": paper[2],
                "total_marks": paper[3],
                "file_path": paper[4],
                "is_ready": True if scheme else False
            }

    return {"error": "Paper not found"}


# ============================================
# GET STUDENT ANALYTICS
# ============================================
@router.get("/analytics/{student_id}")
def get_analytics(student_id: int):
    history = get_student_analytics(student_id)
    return {"history": history}