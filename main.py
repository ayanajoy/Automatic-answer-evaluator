from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi import Request
import traceback
import os

from routes.teacher_routes import router as teacher_router
from routes.student_routes import router as student_router
from routes.auth_routes import router as auth_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= GLOBAL EXCEPTION HANDLER =================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("!!! GLOBAL ERROR CAUGHT !!!")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(exc)},
    )

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

if __name__ == "__main__":
    import uvicorn
    # Use standard host/port for local development
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)