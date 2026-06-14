from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.models.base import Base, TimestampMixin


class Shipment(Base, TimestampMixin):
    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint(
            "shipment_status IN ('pending', 'in_transit', 'delivered', 'returned', 'cancelled')",
            name="shipment_status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True)
    shipment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    order = relationship("Order", back_populates="shipment")
