"""
E-Commerce — Python Enums
Matches the CHECK constraints in the actual Supabase schema.
"""
from __future__ import annotations
import enum


class OrderStatus(str, enum.Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    PACKED    = "packed"
    SHIPPED   = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED  = "returned"
    REFUNDED  = "refunded"


class PaymentStatus(str, enum.Enum):
    PENDING  = "pending"
    PAID     = "paid"
    FAILED   = "failed"
    REFUNDED = "refunded"


class ShipmentStatus(str, enum.Enum):
    PENDING    = "pending"
    PACKED     = "packed"
    IN_TRANSIT = "in_transit"
    DELIVERED  = "delivered"
    RETURNED   = "returned"
