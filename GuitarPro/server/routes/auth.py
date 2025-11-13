from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.models import User
from server import schemas
from server.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from server.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Пользователь с таким email уже существует")

    username = payload.username or payload.email.split("@")[0]
    user = User(email=email, username=username, password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return schemas.RegisterResponse(message="Пользователь успешно создан", user=user)


@router.post("/login", response_model=schemas.TokenResponse)
def login_user(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")

    token = create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=schemas.UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
