from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import os

from routes.teacher_routes import router as teacher_router
from routes.student_routes import router as student_router
from routes.auth_routes import router as auth_router

app = FastAPI()

# ensure uploads folder exists
os.makedirs("uploads", exist_ok=True)

# ================= ROUTERS =================
app.include_router(auth_router)
app.include_router(teacher_router)
app.include_router(student_router)

# ================= STATIC FILES =================
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ================= HOME PAGE =================
@app.get("/")
def home():
    return FileResponse("static/index.html")
