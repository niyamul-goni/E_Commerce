"""
FashionHub — Coupons Router
Endpoints: CRUD, validate coupon
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.models.sales import Coupon
from app.schemas.order import CouponCreate, CouponResponse, CouponValidateRequest, CouponValidateResponse

router = APIRouter(prefix="/coupons", tags=["Coupons"])


@router.get("/", response_model=list[CouponResponse])
def list_coupons(db: Session = Depends(get_db)):
    return db.query(Coupon).filter(Coupon.is_active == True).order_by(Coupon.id).limit(50).all()


@router.post("/", response_model=CouponResponse, status_code=201)
def create_coupon(payload: CouponCreate, db: Session = Depends(get_db)):
    existing = db.query(Coupon).filter(Coupon.code == payload.code.upper()).first()
    if existing:
        raise HTTPException(409, detail="Coupon code already exists")
    coupon = Coupon(**payload.model_dump(), code=payload.code.upper())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.post("/validate", response_model=CouponValidateResponse)
def validate_coupon(payload: CouponValidateRequest, db: Session = Depends(get_db)):
    """
    Validate a coupon code against an order subtotal.
    Uses the apply_coupon PostgreSQL function.
    """
    result = db.execute(
        text("SELECT apply_coupon(:code, :subtotal)"),
        {"code": payload.code.upper(), "subtotal": float(payload.order_subtotal)}
    ).scalar()

    if result == 0:
        return CouponValidateResponse(valid=False, message="Invalid or expired coupon code")

    coupon = db.query(Coupon).filter(Coupon.code == payload.code.upper()).first()
    return CouponValidateResponse(
        valid=True,
        coupon_id=coupon.id if coupon else None,
        discount_amount=Decimal(str(result)),
        message=f"Coupon applied! You save {result:.2f} BDT"
    )


@router.get("/{coupon_id}", response_model=CouponResponse)
def get_coupon(coupon_id: int, db: Session = Depends(get_db)):
    coupon = db.query(Coupon).get(coupon_id)
    if not coupon:
        raise HTTPException(404, detail="Coupon not found")
    return coupon
