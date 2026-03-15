from fastapi import APIRouter
from pydantic import BaseModel
from database import register_user, login_user

router = APIRouter()

# ============================
# REQUEST MODELS
# ============================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ============================
# REGISTER
# ============================

@router.post("/register")
def register(data: RegisterRequest):

    success = register_user(
        data.name,
        data.email,
        data.password,
        data.role
    )

    if success:
        return {"status": "success"}

    return {
        "status": "error",
        "message": "User already exists"
    }


# ============================
# LOGIN
# ============================

@router.post("/login")
def login(data: LoginRequest):

    user = login_user(
        data.email,
        data.password
    )

    if user:

        return {
            "status": "success",
            "user": {
                "id": user[0],
                "name": user[1],
                "role": user[2],
                "email": user[3]
            }
        }

    return {"status": "error"}