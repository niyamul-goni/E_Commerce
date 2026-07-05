"""
E-Commerce — Python Enums
Matches the CHECK constraints in the actual Supabase schema.
"""
from __future__ import annotations
import enum


class OrderStatus(str, enum.Enum):
    PENDING   = "pending"
    PAID      = "paid"
    SHIPPED   = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    FAILED    = "failed"
    REFUNDED  = "refunded"


class ShipmentStatus(str, enum.Enum):
    PENDING    = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED  = "delivered"
    RETURNED   = "returned"
    CANCELLED  = "cancelled"
