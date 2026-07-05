from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.supabase import SupabaseAuthError, get_supabase_user
from app.crud.auth import create_customer, get_customer_by_email
from app.database import get_db
from app.models.customer import Customer
from app.schemas.entities import CustomerCreate
from uuid import uuid4

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def _enrich_customer(customer: Customer, supabase_user: dict) -> Customer:
    """Populate transient metadata fields from Supabase JWT user_metadata."""
    metadata = supabase_user.get("user_metadata") or {}
    customer.first_name = metadata.get("first_name") or "User"
    customer.last_name  = metadata.get("last_name")  or ""
    customer.phone      = metadata.get("phone")
    customer.is_admin   = bool(metadata.get("is_admin", False))
    return customer


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Customer:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        supabase_user = get_supabase_user(token)
        email = supabase_user.get("email")
        if not email:
            raise credentials_exception
    except SupabaseAuthError as exc:
        raise credentials_exception from exc
    except Exception as exc:
        raise credentials_exception from exc

    user = get_customer_by_email(db, email)
    if user is None:
        # Auto-create the customer row on first login
        metadata = supabase_user.get("user_metadata") or {}
        user = create_customer(
            db,
            CustomerCreate(
                first_name=metadata.get("first_name") or "User",
                last_name=metadata.get("last_name")  or "",
                email=email,
                phone=metadata.get("phone"),
                password=uuid4().hex,
                is_active=True,
                is_admin=bool(metadata.get("is_admin", False)),
            ),
        )

    if user is None:
        raise credentials_exception

    # Always re-populate transient metadata from the JWT (they aren't in the DB)
    _enrich_customer(user, supabase_user)
    return user


def require_admin(current_user: Customer = Depends(get_current_user)) -> Customer:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
