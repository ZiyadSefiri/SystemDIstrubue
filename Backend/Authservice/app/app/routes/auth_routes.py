from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user_model import User
from app.utils.auth_utils import verify_password
from app.config import get_db

security = HTTPBearer()

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

def create_user(user: User, db: Session):
    user.password = verify_password(user.password)
    try:
        db.add(user)
        db.commit()
        return user
    except IntegrityError:
        db.rollback()
        raise