from __future__ import annotations

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.crud.auth import create_customer
from app.crud.base import CRUDBase
from app.models.category import Category
from app.models.customer import Customer
from app.models.product import Product
from app.models.supplier import Supplier
from app.schemas.entities import (
    CategoryCreate,
    CategoryUpdate,
    CustomerCreate,
    CustomerUpdate,
    ProductCreate,
    ProductUpdate,
    SupplierCreate,
    SupplierUpdate,
)

customer = CRUDBase[Customer, CustomerCreate, CustomerUpdate](Customer)
category = CRUDBase[Category, CategoryCreate, CategoryUpdate](Category)
supplier = CRUDBase[Supplier, SupplierCreate, SupplierUpdate](Supplier)
product = CRUDBase[Product, ProductCreate, ProductUpdate](Product)


def create_new_customer(db: Session, customer_in: CustomerCreate) -> Customer:
    return create_customer(db, customer_in)


def search_products(
    db: Session,
    *,
    query: Optional[str] = None,
    category_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> list[Product]:
    products_query = db.query(Product)
    if query:
        pattern = f"%{query}%"
        products_query = products_query.filter(or_(Product.name.ilike(pattern), Product.sku.ilike(pattern)))
    if category_id is not None:
        products_query = products_query.filter(Product.category_id == category_id)
    if supplier_id is not None:
        products_query = products_query.filter(Product.supplier_id == supplier_id)
    if min_price is not None:
        products_query = products_query.filter(Product.price >= min_price)
    if max_price is not None:
        products_query = products_query.filter(Product.price <= max_price)
    return products_query.order_by(Product.name.asc()).all()
