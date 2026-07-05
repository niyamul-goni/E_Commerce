"""
Customer model — matches the ACTUAL Supabase `customers` table.
The real schema has: id, email, password_hash, is_active, email_verified, created_at, updated_at
first_name/last_name live in customer_profiles; we attach them as transient attrs from JWT.
"""
from __future__ import annotations

from typing import ClassVar, Optional

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Customer(Base):
    __tablename__ = "customers"
    __allow_unmapped__ = True

    id            = Column(Integer, primary_key=True, autoincrement=True)
    email         = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False, default="supabase_managed")
    is_active     = Column(Boolean, default=True, nullable=False)

    # Transient metadata fields — NOT mapped to DB columns.
    # Populated by auth dependencies from Supabase JWT user_metadata.
    first_name: ClassVar[str]
    last_name:  ClassVar[str]
    is_admin:   ClassVar[bool]
    phone:      ClassVar[Optional[str]]
