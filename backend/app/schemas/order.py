"""
FashionHub — Pydantic Schemas
Order, OrderItem, Payment, Shipment, Invoice, Coupon, Return, Refund schemas
"""
from __future__ import annotations
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================
# COUPON SCHEMAS
# ============================================================

class CouponBase(BaseModel):
    code: str = Field(..., max_length=50)
    coupon_type: str
    value: Decimal
    min_order_amount: Decimal = Decimal("0")
    max_discount_amount: Optional[Decimal] = None
    max_uses: int = 1
    description: Optional[str] = None


class CouponCreate(CouponBase):
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None


class CouponValidateRequest(BaseModel):
    code: str
    order_subtotal: Decimal


class CouponValidateResponse(BaseModel):
    valid: bool
    coupon_id: Optional[int] = None
    discount_amount: Optional[Decimal] = None
    message: str


class CouponResponse(CouponBase):
    id: int
    used_count: int
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================
# ORDER SCHEMAS
# ============================================================

class OrderItemCreate(BaseModel):
    variant_id: int
    quantity: int = Field(..., gt=0, le=100)


class OrderItemResponse(BaseModel):
    id: int
    variant_id: int
    quantity: int
    unit_price: Decimal
    line_total: Optional[Decimal] = None    # GENERATED COLUMN
    product_name: Optional[str] = None
    color_name: Optional[str] = None
    size_name: Optional[str] = None
    sku: Optional[str] = None

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    shipping_address_id: int
    billing_address_id: Optional[int] = None
    shipping_method_id: int
    coupon_code: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_length=1)
    notes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class OrderSummaryResponse(BaseModel):
    """Compact response for order listing"""
    id: int
    order_number: str
    status: str
    total_amount: Decimal
    item_count: int
    order_date: Optional[str] = None
    payment_status: Optional[str] = None

    class Config:
        from_attributes = True


class OrderDetailResponse(BaseModel):
    """Full order detail"""
    id: int
    order_number: str
    customer_id: int
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    shipping_cost: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    order_date: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemResponse] = []
    payment: Optional["PaymentResponse"] = None
    shipment: Optional["ShipmentResponse"] = None
    invoice: Optional["InvoiceResponse"] = None

    class Config:
        from_attributes = True


# ============================================================
# PAYMENT SCHEMAS
# ============================================================

class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str
    amount: Decimal
    transaction_ref: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    payment_method: str
    payment_status: str
    amount: Decimal
    transaction_ref: Optional[str] = None
    paid_at: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# SHIPMENT SCHEMAS
# ============================================================

class ShipmentCreate(BaseModel):
    order_id: int
    shipping_method_id: int
    tracking_number: Optional[str] = None
    carrier_name: Optional[str] = None


class ShipmentStatusUpdate(BaseModel):
    shipment_status: str
    tracking_number: Optional[str] = None


class ShipmentResponse(BaseModel):
    id: int
    order_id: int
    tracking_number: Optional[str] = None
    carrier_name: Optional[str] = None
    shipment_status: str
    shipped_at: Optional[str] = None
    estimated_delivery: Optional[str] = None
    delivered_at: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# INVOICE SCHEMAS
# ============================================================

class InvoiceResponse(BaseModel):
    id: int
    order_id: int
    invoice_number: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    issued_at: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# RETURN & REFUND SCHEMAS
# ============================================================

class ReturnRequestCreate(BaseModel):
    order_id: int
    reason: str


class ReturnRequestResponse(BaseModel):
    id: int
    order_id: int
    customer_id: int
    reason: str
    status: str
    resolved_at: Optional[str] = None
    refund: Optional["RefundResponse"] = None

    class Config:
        from_attributes = True


class RefundCreate(BaseModel):
    return_request_id: int
    refund_amount: Decimal
    refund_method: str
    notes: Optional[str] = None


class RefundResponse(BaseModel):
    id: int
    return_request_id: int
    refund_amount: Decimal
    refund_method: str
    status: str
    transaction_ref: Optional[str] = None
    processed_at: Optional[str] = None

    class Config:
        from_attributes = True


# Update forward references
OrderDetailResponse.model_rebuild()
ReturnRequestResponse.model_rebuild()
