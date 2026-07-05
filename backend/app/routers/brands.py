"""
FashionHub — Brands Router
Endpoints: GET, POST, PUT brands
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.catalog import Brand
from app.schemas.product import BrandResponse, BrandCreate, BrandUpdate

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("/", response_model=List[BrandResponse])
def list_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List all brands with optional active filter."""
    q = db.query(Brand)
    if is_active is not None:
        q = q.filter(Brand.is_active == is_active)
    return q.order_by(Brand.name).offset(skip).limit(limit).all()


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(Brand).get(brand_id)
    if not brand:
        raise HTTPException(404, detail=f"Brand {brand_id} not found")
    return brand


@router.post("/", response_model=BrandResponse, status_code=201)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    existing = db.query(Brand).filter(Brand.slug == payload.slug).first()
    if existing:
        raise HTTPException(409, detail="Brand slug already exists")
    brand = Brand(**payload.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


@router.put("/{brand_id}", response_model=BrandResponse)
def update_brand(brand_id: int, payload: BrandUpdate, db: Session = Depends(get_db)):
    brand = db.query(Brand).get(brand_id)
    if not brand:
        raise HTTPException(404, detail="Brand not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(brand, field, value)
    db.commit()
    db.refresh(brand)
    return brand
