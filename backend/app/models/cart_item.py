"""
CartItem model — matches the actual Supabase `cart_items` table.
"""
from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    product_id  = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity    = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("customer_id", "product_id", name="uq_cart_items_customer_product"),
    )

    # Relationships
    customer = relationship("Customer", back_populates="cart_items")
