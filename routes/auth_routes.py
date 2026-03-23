from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from database import register_user, get_user_by_email
from dependencies import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(data: RegisterRequest):
    hashed_pwd = get_password_hash(data.password)
    success = register_user(data.name, data.email, hashed_pwd, data.role)
    if success:
        return {"status": "success"}
    return {"status": "error", "message": "User already exists"}

@router.post("/login")
def login(data: LoginRequest):
    user = get_user_by_email(data.email)
    if not user or not verify_password(data.password, user[4]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user[0])})
    
    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "role": user[3]
        }
    }