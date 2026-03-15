from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import os
import uvicorn

from routes.teacher_routes import router as teacher_router
from routes.student_routes import router as student_router
from routes.auth_routes import router as auth_router

app = FastAPI()

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


# ================= START SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
