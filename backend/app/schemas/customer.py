"""
FashionHub — Pydantic Schemas
Customer, Auth, Review schemas
"""
from __future__ import annotations
from decimal import Decimal
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr, Field


# ============================================================
# AUTH SCHEMAS
# ============================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: Optional[str] = None



class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_id: int
    email: str


# ============================================================
# CUSTOMER SCHEMAS
# ============================================================

class CustomerProfileBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender_id: Optional[int] = None


class CustomerProfileUpdate(CustomerProfileBase):
    pass


class AddressCreate(BaseModel):
    label: str = "Home"
    recipient_name: str = Field(..., max_length=150)
    phone: Optional[str] = None
    line1: str = Field(..., max_length=255)
    line2: Optional[str] = None
    city: str = Field(..., max_length=100)
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Bangladesh"
    is_default: bool = False


class AddressResponse(AddressCreate):
    id: int
    customer_id: int

    class Config:
        from_attributes = True


class CustomerResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    email_verified: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# WISHLIST & CART SCHEMAS
# ============================================================

class WishlistItemCreate(BaseModel):
    variant_id: int


class WishlistItemResponse(BaseModel):
    id: int
    variant_id: int
    product_name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[Decimal] = None
    primary_image_url: Optional[str] = None

    class Config:
        from_attributes = True


class CartItemCreate(BaseModel):
    variant_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, le=100)


class CartItemResponse(BaseModel):
    id: int
    variant_id: int
    quantity: int
    product_name: Optional[str] = None
    color_name: Optional[str] = None
    size_name: Optional[str] = None
    unit_price: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    available_stock: int = 0
    primary_image_url: Optional[str] = None

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    customer_id: int
    items: List[CartItemResponse] = []
    item_count: int = 0
    subtotal: Decimal = Decimal("0")

    class Config:
        from_attributes = True


# ============================================================
# REVIEW SCHEMAS
# ============================================================

class ReviewCreate(BaseModel):
    variant_id: int
    order_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    customer_id: int
    variant_id: int
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    is_approved: bool
    is_verified: bool
    customer_name: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class ReviewReplyCreate(BaseModel):
    review_id: int
    body: str
