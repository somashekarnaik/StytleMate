from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import (
    SESSION_COOKIE,
    SESSION_SECONDS,
    create_session_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    password: str = Field(min_length=12, max_length=128)


def _user_response(user: User) -> dict[str, object]:
    return {"id": user.id, "email": user.email}


def _start_session(response: Response, user: User) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(user.id),
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    credentials: Credentials,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    email = str(credentials.email).strip().lower()
    user = User(email=email, password_hash=hash_password(credentials.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None
    _start_session(response, user)
    return {"user": _user_response(user)}


@router.post("/login")
def login(
    credentials: Credentials,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    email = str(credentials.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
        )
    _start_session(response, user)
    return {"user": _user_response(user)}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.get("/me")
def current_user(user: Annotated[User, Depends(get_current_user)]) -> dict[str, object]:
    return {"user": _user_response(user)}
