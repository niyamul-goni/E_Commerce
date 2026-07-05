"""
Shipment model — matches the actual Supabase `shipments` table.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    order_id        = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    carrier         = Column(String(100))
    tracking_number = Column(String(120), unique=True)
    shipment_status = Column(String(20), nullable=False, default="pending")
    shipped_at      = Column(DateTime(timezone=True))
    delivered_at    = Column(DateTime(timezone=True))

    # Relationships
    order = relationship("Order")
