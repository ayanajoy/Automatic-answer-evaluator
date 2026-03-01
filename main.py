from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes.teacher_routes import router as teacher_router
from routes.student_routes import router as student_router

app = FastAPI()

# Include routers
app.include_router(teacher_router)
app.include_router(student_router)

# Serve static pages
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def home():
    return {"message": "Automatic Answer Checker API Running"}