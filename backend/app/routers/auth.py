from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.security import create_access_token
from app.crud.auth import authenticate_customer, create_customer, get_customer_by_email
from app.database import get_db
from app.schemas import CustomerRead, CustomerCreate, LoginRequest, RegisterRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(register_in: RegisterRequest, db: Session = Depends(get_db)) -> Token:
    if get_customer_by_email(db, register_in.email) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    customer = create_customer(db, CustomerCreate(**register_in.model_dump()))
    access_token = create_access_token(customer.id)
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    customer = authenticate_customer(db, form_data.username, form_data.password)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(customer.id)
    return Token(access_token=access_token)


@router.get("/me", response_model=CustomerRead)
def read_current_user(current_user=Depends(get_current_user)) -> CustomerRead:
    return current_user
