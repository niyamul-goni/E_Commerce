"""
Supplier model — matches the actual Supabase `suppliers` table.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, String

from app.models.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(150), nullable=False, unique=True)
    contact_email = Column(String(255), unique=True)
    contact_phone = Column(String(30), unique=True)
    address       = Column(String(500))
    is_active     = Column(Boolean, default=True, nullable=False)
