"""
Review model — matches the actual Supabase `reviews` table.
"""
from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    product_id  = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    rating      = Column(Integer, nullable=False)
    comment     = Column(Text)

    __table_args__ = (
        UniqueConstraint("customer_id", "product_id", name="uq_reviews_customer_product"),
    )

    # Relationships
    customer = relationship("Customer", back_populates="reviews")
