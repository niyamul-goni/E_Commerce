from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.crud.auth import get_customer_by_email
from app.database import get_db
from app.core.supabase import SupabaseAuthError, create_supabase_user, login_supabase_user
from app.schemas import CustomerRead, RegisterRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(register_in: RegisterRequest, db: Session = Depends(get_db)) -> Token:
    if get_customer_by_email(db, register_in.email) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    try:
        create_supabase_user(
            email=register_in.email,
            password=register_in.password,
            user_metadata={
                "first_name": register_in.first_name,
                "last_name": register_in.last_name,
                "phone": register_in.phone,
            },
        )
    except SupabaseAuthError as exc:
        # If the user already exists in Supabase (e.g. from a prior partial
        # signup), fall through and try to log them in instead of failing.
        if exc.status_code != 422:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    try:
        session = login_supabase_user(email=register_in.email, password=register_in.password)
    except SupabaseAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return Token(access_token=session["access_token"])


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    try:
        session = login_supabase_user(email=form_data.username, password=form_data.password)
    except SupabaseAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return Token(access_token=session["access_token"])


@router.get("/me", response_model=CustomerRead)
def read_current_user(current_user=Depends(get_current_user)) -> CustomerRead:
    return current_user
