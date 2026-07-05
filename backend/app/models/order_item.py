"""
OrderItem model — matches the actual Supabase `order_items` table.
"""
from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    order_id   = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity   = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_order_items_order_product"),
    )

    # Relationships
    order = relationship("Order", back_populates="items")
