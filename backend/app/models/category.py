"""
Category model — matches the actual Supabase `categories` table.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, String

from app.models.base import Base


class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(120), nullable=False, unique=True)
    description = Column(String(500))
    is_active   = Column(Boolean, default=True, nullable=False)
