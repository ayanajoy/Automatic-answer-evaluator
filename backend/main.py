from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from nlp.similarity import calculate_similarity, calculate_marks
from database import save_result, get_all_results

app = FastAPI()

# -----------------------------
# Request Model
# -----------------------------
class AnswerRequest(BaseModel):
    model_answer: str
    student_answer: str
    total_marks: float


# -----------------------------
# Home Route
# -----------------------------
@app.get("/")
def home():
    return {"message": "Automatic Answer Checker API Running"}


# -----------------------------
# Evaluate Answer
# -----------------------------
@app.post("/evaluate")
def evaluate_answer(data: AnswerRequest):

    similarity = calculate_similarity(
        data.model_answer,
        data.student_answer
    )

    marks = calculate_marks(similarity, data.total_marks)

    # Save result in database
    save_result(
        data.model_answer,
        data.student_answer,
        similarity,
        marks,
        data.total_marks
    )

    return {
        "similarity": round(similarity, 4),
        "marks": marks,
        "total_marks": data.total_marks
    }


# -----------------------------
# View All Results
# -----------------------------
@app.get("/results")
def view_results():
    return get_all_results()


# -----------------------------
# Serve Static HTML Files
# -----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")