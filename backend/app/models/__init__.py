"""
E-Commerce — SQLAlchemy Models
Models matching the actual Supabase database schema (10 tables).
"""
from __future__ import annotations

# Base must be exported so that database.py can do: from app.models import Base
from app.models.base import Base  # noqa: F401

from app.models.customer import Customer
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.shipment import Shipment
from app.models.review import Review
from app.models.cart_item import CartItem

__all__ = [
    "Base",
    "Customer",
    "Category",
    "Supplier",
    "Product",
    "Order",
    "OrderItem",
    "Payment",
    "Shipment",
    "Review",
    "CartItem",
]
