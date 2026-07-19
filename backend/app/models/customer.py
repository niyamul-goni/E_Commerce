"""
Customer model — matches the ACTUAL Supabase `customers` table.
Columns: id, email, password_hash, is_active, email_verified, is_admin, created_at, updated_at
first_name/last_name live in customer_profiles; we attach them as transient attrs from JWT.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Customer(Base):
    __tablename__ = "customers"
    __allow_unmapped__ = True

    id             = Column(Integer, primary_key=True, autoincrement=True)
    email          = Column(String(255), nullable=False, unique=True)
    password_hash  = Column(String(255), nullable=False, default="supabase_managed")
    is_active      = Column(Boolean, default=True,  nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    is_admin       = Column(Boolean, default=False, nullable=False)
    created_at     = Column(DateTime(timezone=True), nullable=True)
    updated_at     = Column(DateTime(timezone=True), nullable=True)

    # Relationships referenced by other models via back_populates
    orders     = relationship("Order",    back_populates="customer", lazy="dynamic")
    reviews    = relationship("Review",   back_populates="customer", lazy="dynamic")
    cart_items = relationship("CartItem", back_populates="customer", lazy="dynamic")

    # Transient metadata fields — NOT mapped to DB columns.
    # Populated by auth dependencies from Supabase JWT user_metadata.
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.first_name: str = "User"
        self.last_name: str  = ""
        self.phone: Optional[str] = None
