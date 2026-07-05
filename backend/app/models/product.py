"""
Product model — matches the actual Supabase `products` table,
including the `available_sizes` column added via migration.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    name            = Column(String(200), nullable=False)
    sku             = Column(String(80), nullable=False, unique=True)
    description     = Column(Text)
    price           = Column(Numeric(12, 2), nullable=False)
    stock_quantity  = Column(Integer, nullable=False, default=0)
    is_active       = Column(Boolean, default=True, nullable=False)
    category_id     = Column(Integer, ForeignKey("categories.id"), nullable=False)
    supplier_id     = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    available_sizes = Column(String(500), nullable=True)

    # Relationships — NOTE: Product queries use raw SQL; ORM relationships kept
    # minimal to avoid mapper configuration errors.
    reviews    = relationship("Review",    foreign_keys="Review.product_id")
    cart_items = relationship("CartItem",  foreign_keys="CartItem.product_id")
    order_items = relationship("OrderItem", foreign_keys="OrderItem.product_id")
