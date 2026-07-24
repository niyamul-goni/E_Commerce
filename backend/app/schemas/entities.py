from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.models.enums import OrderStatus, PaymentStatus, ShipmentStatus
from app.schemas.common import ORMModel


class RegisterRequest(ORMModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        digits = re.sub(r"\D", "", v)
        if len(digits) != 11:
            raise ValueError("Phone number must be exactly 11 digits")
        if not digits.startswith("0"):
            raise ValueError("Phone number must start with 0 (e.g. 01775529619)")
        return digits



class LoginRequest(ORMModel):
    email: EmailStr
    password: str


class CustomerCreate(RegisterRequest):
    is_active: bool = True
    is_admin: bool = False


class CustomerUpdate(ORMModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class CustomerRead(ORMModel):
    id: int
    first_name: Optional[str] = "User"
    last_name: Optional[str] = ""
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool
    is_admin: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CategoryCreate(ORMModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = True


class CategoryUpdate(ORMModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class CategoryRead(ORMModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SubcategoryCreate(ORMModel):
    category_id: int
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0, le=32_767)


class SubcategoryUpdate(ORMModel):
    category_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(default=None, ge=0, le=32_767)


class SupplierCreate(ORMModel):
    name: str = Field(min_length=1, max_length=150)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = True


class SupplierUpdate(ORMModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(default=None, max_length=30)
    address: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class SupplierRead(ORMModel):
    id: int
    name: str
    contact_email: Optional[str]
    contact_phone: Optional[str]
    address: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductCreate(ORMModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(min_length=1, max_length=80)
    description: Optional[str] = None
    price: Decimal = Field(gt=0)
    stock_quantity: int = Field(ge=0)
    category_id: int
    supplier_id: int
    brand_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    is_active: bool = True
    available_sizes: Optional[str] = Field(default=None, max_length=500)


class ProductUpdate(ORMModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    sku: Optional[str] = Field(default=None, min_length=1, max_length=80)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, gt=0)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    brand_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    is_active: Optional[bool] = None
    available_sizes: Optional[str] = Field(default=None, max_length=500)


class ProductRead(ORMModel):
    id: int
    name: str
    sku: str
    description: Optional[str]
    price: Decimal
    stock_quantity: int
    is_active: bool
    category_id: int
    supplier_id: int
    available_sizes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OrderItemCreate(ORMModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderItemRead(ORMModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class OrderCreate(ORMModel):
    customer_id: int
    shipping_address: str = Field(min_length=1, max_length=500)
    billing_address: Optional[str] = Field(default=None, max_length=500)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(ORMModel):
    status: OrderStatus


class OrderRead(ORMModel):
    id: int
    order_number: str
    customer_id: int
    status: str
    total_amount: Decimal
    shipping_address: str
    billing_address: Optional[str]
    order_date: datetime
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = Field(default_factory=list)


class PaymentCreate(ORMModel):
    order_id: int
    amount: Decimal = Field(gt=0)
    payment_method: str = Field(min_length=1, max_length=50)
    payment_status: PaymentStatus = PaymentStatus.PENDING
    transaction_reference: Optional[str] = Field(default=None, max_length=120)


class PaymentRead(ORMModel):
    id: int
    order_id: int
    amount: Decimal
    payment_method: str
    payment_status: str
    transaction_reference: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ShipmentCreate(ORMModel):
    order_id: int
    carrier: Optional[str] = Field(default=None, max_length=100)
    tracking_number: Optional[str] = Field(default=None, max_length=120)
    shipment_status: ShipmentStatus = ShipmentStatus.PENDING


class ShipmentRead(ORMModel):
    id: int
    order_id: int
    carrier: Optional[str]
    tracking_number: Optional[str]
    shipment_status: str
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ReviewCreate(ORMModel):
    customer_id: int
    product_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)


class ReviewRead(ORMModel):
    id: int
    customer_id: int
    product_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime


class CartItemCreate(ORMModel):
    customer_id: int
    product_id: int
    quantity: int = Field(gt=0)


class CartItemUpdate(ORMModel):
    quantity: int = Field(gt=0)


class CartItemRead(ORMModel):
    id: int
    customer_id: int
    product_id: int
    quantity: int
    created_at: datetime
    updated_at: datetime
