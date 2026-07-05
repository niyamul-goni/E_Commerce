"""
Order model — matches the actual Supabase `orders` table.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    order_number     = Column(String(40), nullable=False, unique=True)
    customer_id      = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status           = Column(String(20), nullable=False, default="pending")
    total_amount     = Column(Numeric(12, 2), nullable=False, default=0)
    shipping_address = Column(String(500), nullable=False)
    billing_address  = Column(String(500))
    order_date       = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items    = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
