from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Import Teacher Router
from routes.teacher_routes import router as teacher_router

app = FastAPI()

# Include Teacher Routes
app.include_router(teacher_router)

# Serve Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return {"message": "Automatic Answer Checker API Running"}