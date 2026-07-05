from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.customer import Customer
from app.schemas.entities import CustomerCreate, CustomerUpdate


def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
    return db.query(Customer).filter(Customer.email == email).first()


def authenticate_customer(db: Session, email: str, password: str) -> Optional[Customer]:
    customer = get_customer_by_email(db, email)
    if customer is None:
        return None
    if not verify_password(password, customer.password_hash):
        return None
    return customer


def create_customer(db: Session, customer_in: CustomerCreate) -> Customer:
    """Create a minimal customer row matching the actual Supabase schema."""
    customer = Customer(
        email=customer_in.email,
        password_hash=get_password_hash(customer_in.password),
        is_active=customer_in.is_active,
    )
    # Attach metadata as Python attributes (not DB columns)
    customer.first_name = customer_in.first_name
    customer.last_name  = customer_in.last_name
    customer.phone      = customer_in.phone
    customer.is_admin   = customer_in.is_admin

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # Re-attach metadata after refresh (SQLAlchemy refresh resets Python attrs)
    customer.first_name = customer_in.first_name
    customer.last_name  = customer_in.last_name
    customer.phone      = customer_in.phone
    customer.is_admin   = customer_in.is_admin
    return customer


def update_customer(db: Session, customer: Customer, customer_in: CustomerUpdate) -> Customer:
    data = customer_in.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    # Only update DB columns that exist in the real schema
    for field_name in ("email", "is_active"):
        if field_name in data:
            setattr(customer, field_name, data[field_name])
    # Update metadata attributes
    if "first_name" in data:
        customer.first_name = data["first_name"]
    if "last_name" in data:
        customer.last_name = data["last_name"]
    if "phone" in data:
        customer.phone = data["phone"]
    if "is_admin" in data:
        customer.is_admin = data["is_admin"]
    if password is not None:
        customer.password_hash = get_password_hash(password)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
