# Backend/AuthService/authentifcation.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from Utility.connect import connect_database
from passlib.hash import bcrypt
from jose import jwt  # ✅ use python-jose
from datetime import datetime, timedelta

# ---- Setup ----
app = FastAPI(title="Auth Service")
engine = connect_database()

SECRET_KEY = "YOUR_SECRET_KEY"  # 🔒 Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# ---- Pydantic Models ----
class RegisterUser(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: str | None = None

class LoginUser(BaseModel):
    email: EmailStr
    password: str

# ---- Helper ----
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ---- Endpoints ----
@app.post("/register")
def register(user: RegisterUser):
    with engine.connect() as conn:
        existing = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": user.email}).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pw = bcrypt.hash(user.password)

        conn.execute(
            text("""
                INSERT INTO users (name, email, password_hash, phone_number)
                VALUES (:name, :email, :password_hash, :phone_number)
            """),
            {
                "name": user.name,
                "email": user.email,
                "password_hash": hashed_pw,
                "phone_number": user.phone_number
            }
        )
        conn.commit()

    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: LoginUser):
    with engine.connect() as conn:
        record = conn.execute(
            text("SELECT user_id, name, password_hash FROM users WHERE email = :email"),
            {"email": user.email}
        ).fetchone()

        if not record:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id, name, hashed_pw = record

        if not bcrypt.verify(user.password, hashed_pw):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"sub": str(user_id), "name": name})

    return {"access_token": token, "token_type": "bearer"}
