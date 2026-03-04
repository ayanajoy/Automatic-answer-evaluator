from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routes.teacher_routes import router as teacher_router
from routes.student_routes import router as student_router

app = FastAPI()

# ================= ROUTERS =================
app.include_router(teacher_router)
app.include_router(student_router)

# ================= STATIC FILES =================
app.mount("/static", StaticFiles(directory="static"), name="static")

# uploaded question papers / answers
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ================= HOME PAGE =================
@app.get("/")
def home():
    return FileResponse("static/index.html")