from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.routes.auth_routes import authenticate_user, create_user
from app.models.user_model import User
from app.utils.auth_utils import verify_password, create_access_token
from app.config import get_db

app = FastAPI()

security = HTTPBearer()

@app.post("/register")
def register_user(user: User, db: Session = Depends(get_db)):
    try:
        user.password = verify_password(user.password)
        user_db = create_user(user, db)
        return {"message": "User registered successfully", "user_id": user_db.id}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")

@app.post("/login")
def login_user(username: str, password: str, db: Session = Depends(get_db)):
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload["sub"]
        return {"message": "User authenticated successfully", "username": username}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")