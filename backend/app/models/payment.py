"""
Payment model — matches the actual Supabase `payments` table.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    order_id              = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    amount                = Column(Numeric(12, 2), nullable=False)
    payment_method        = Column(String(50), nullable=False)
    payment_status        = Column(String(20), nullable=False, default="pending")
    transaction_reference = Column(String(120), unique=True)
    paid_at               = Column(DateTime(timezone=True))

    # Relationships
    order = relationship("Order")
