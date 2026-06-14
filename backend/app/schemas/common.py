from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DashboardSummary(BaseModel):
    total_customers: int
    total_categories: int
    total_suppliers: int
    total_products: int
    total_orders: int
    total_sales: Decimal
    total_payments: Decimal
    total_cart_items: int
    average_order_value: Decimal
    low_stock_products: int
    top_rated_products: int
    pending_orders: int
    shipped_orders: int
