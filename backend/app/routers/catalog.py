from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.crud.catalog import category, create_new_customer, customer, product, search_products, supplier
from app.crud.auth import create_customer, update_customer as update_customer_record
from app.database import get_db
from app.models.category import Category
from app.models.customer import Customer
from app.models.product import Product
from app.models.supplier import Supplier
from app.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    Message,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
)

customers_router = APIRouter(prefix="/customers", tags=["customers"])
categories_router = APIRouter(prefix="/categories", tags=["categories"])
suppliers_router = APIRouter(prefix="/suppliers", tags=["suppliers"])
products_router = APIRouter(prefix="/products", tags=["products"])


@customers_router.get("", response_model=list[CustomerRead], dependencies=[Depends(require_admin)])
def list_customers(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> list[Customer]:
    return customer.get_multi(db, skip=skip, limit=limit)


@customers_router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_customer_endpoint(customer_in: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    return create_new_customer(db, customer_in)


@customers_router.get("/{customer_id}", response_model=CustomerRead, dependencies=[Depends(require_admin)])
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> Customer:
    db_customer = customer.get(db, customer_id)
    if db_customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return db_customer


@customers_router.put("/{customer_id}", response_model=CustomerRead, dependencies=[Depends(require_admin)])
def update_customer(customer_id: int, customer_in: CustomerUpdate, db: Session = Depends(get_db)) -> Customer:
    db_customer = customer.get(db, customer_id)
    if db_customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return update_customer_record(db, db_customer, customer_in)


@customers_router.delete("/{customer_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_customer(customer_id: int, db: Session = Depends(get_db)) -> Message:
    deleted = customer.remove(db, object_id=customer_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return Message(message="Customer deleted successfully")


@categories_router.get("", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> list[Category]:
    return category.get_multi(db, skip=skip, limit=limit)


@categories_router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_category(category_in: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    return category.create(db, obj_in=category_in)


@categories_router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)) -> Category:
    db_category = category.get(db, category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return db_category


@categories_router.put("/{category_id}", response_model=CategoryRead, dependencies=[Depends(require_admin)])
def update_category(category_id: int, category_in: CategoryUpdate, db: Session = Depends(get_db)) -> Category:
    db_category = category.get(db, category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category.update(db, db_obj=db_category, obj_in=category_in)


@categories_router.delete("/{category_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_category(category_id: int, db: Session = Depends(get_db)) -> Message:
    deleted = category.remove(db, object_id=category_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return Message(message="Category deleted successfully")


@suppliers_router.get("", response_model=list[SupplierRead])
def list_suppliers(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> list[Supplier]:
    return supplier.get_multi(db, skip=skip, limit=limit)


@suppliers_router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_supplier(supplier_in: SupplierCreate, db: Session = Depends(get_db)) -> Supplier:
    return supplier.create(db, obj_in=supplier_in)


@suppliers_router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)) -> Supplier:
    db_supplier = supplier.get(db, supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return db_supplier


@suppliers_router.put("/{supplier_id}", response_model=SupplierRead, dependencies=[Depends(require_admin)])
def update_supplier(supplier_id: int, supplier_in: SupplierUpdate, db: Session = Depends(get_db)) -> Supplier:
    db_supplier = supplier.get(db, supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier.update(db, db_obj=db_supplier, obj_in=supplier_in)


@suppliers_router.delete("/{supplier_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)) -> Message:
    deleted = supplier.remove(db, object_id=supplier_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return Message(message="Supplier deleted successfully")


@products_router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> list[Product]:
    return product.get_multi(db, skip=skip, limit=limit)


@products_router.get("/search", response_model=list[ProductRead])
def search_products_endpoint(
    db: Session = Depends(get_db),
    query: Optional[str] = None,
    category_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> list[Product]:
    return search_products(
        db,
        query=query,
        category_id=category_id,
        supplier_id=supplier_id,
        min_price=min_price,
        max_price=max_price,
    )


@products_router.get("/category/{category_id}", response_model=list[ProductRead])
def filter_products_by_category(category_id: int, db: Session = Depends(get_db)) -> list[Product]:
    return product.get_multi(db, skip=0, limit=100) if category_id is None else db.query(Product).filter(Product.category_id == category_id).all()


@products_router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)) -> Product:
    return product.create(db, obj_in=product_in)


@products_router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    db_product = product.get(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return db_product


@products_router.put("/{product_id}", response_model=ProductRead, dependencies=[Depends(require_admin)])
def update_product(product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)) -> Product:
    db_product = product.get(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product.update(db, db_obj=db_product, obj_in=product_in)


@products_router.delete("/{product_id}", response_model=Message, dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)) -> Message:
    deleted = product.remove(db, object_id=product_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return Message(message="Product deleted successfully")
