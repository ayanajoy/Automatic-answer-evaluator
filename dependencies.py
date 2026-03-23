from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import get_connection

SECRET_KEY = "supersecretkey_please_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# We use bcrypt directly because passlib has compatibility issues with newer bcrypt/Python versions
def verify_password(plain_password, hashed_password):
    if isinstance(hashed_password, str):
        # Backward compatibility for legacy users with plaintext passwords
        return plain_password == hashed_password
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)
    except Exception:
        return False

def get_password_hash(password):
    # bcrypt.hashpw returns a bytes object
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user is None:
        raise credentials_exception

    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "role": user[3]
    }

def get_current_teacher(current_user: dict = Depends(get_current_user)):
    role = str(current_user.get("role", "")).lower()
    if role != "teacher":
        print(f"!!! 403 FORBIDDEN: User {current_user['email']} has role '{role}', but 'teacher' is required.")
        raise HTTPException(status_code=403, detail="Teachers only")
    return current_user

def get_current_student(current_user: dict = Depends(get_current_user)):
    role = str(current_user.get("role", "")).lower()
    if role != "student":
        print(f"!!! 403 FORBIDDEN: User {current_user['email']} has role '{role}', but 'student' is required.")
        raise HTTPException(status_code=403, detail="Students only")
    return current_user