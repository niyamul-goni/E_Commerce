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
    customer = Customer(
        first_name=customer_in.first_name,
        last_name=customer_in.last_name,
        email=customer_in.email,
        phone=customer_in.phone,
        password_hash=get_password_hash(customer_in.password),
        is_active=customer_in.is_active,
        is_admin=customer_in.is_admin,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, customer: Customer, customer_in: CustomerUpdate) -> Customer:
    data = customer_in.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    for field_name, value in data.items():
        setattr(customer, field_name, value)
    if password is not None:
        customer.password_hash = get_password_hash(password)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
