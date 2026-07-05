"""
FashionHub — Pydantic Schemas
Product, Variant, Inventory, Brand, Category schemas
"""
from __future__ import annotations
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


# ============================================================
# BRAND SCHEMAS
# ============================================================

class BrandBase(BaseModel):
    name: str = Field(..., max_length=150)
    slug: str = Field(..., max_length=150)
    country_of_origin: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    country_of_origin: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BrandResponse(BrandBase):
    id: int
    is_active: bool
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# SUPPLIER SCHEMAS
# ============================================================

class SupplierBase(BaseModel):
    name: str = Field(..., max_length=150)
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    country: Optional[str] = None
    lead_time_days: int = 14
    reliability_score: Optional[Decimal] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierResponse(SupplierBase):
    id: int

    class Config:
        from_attributes = True


# ============================================================
# CATEGORY SCHEMAS
# ============================================================

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=120)
    slug: str = Field(..., max_length=120)
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class SubCategoryBase(BaseModel):
    name: str = Field(..., max_length=120)
    slug: str = Field(..., max_length=120)
    category_id: int


class SubCategoryResponse(SubCategoryBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================
# PRODUCT SCHEMAS
# ============================================================

class ProductImageResponse(BaseModel):
    id: int
    image_url: str
    alt_text: Optional[str] = None
    is_primary: bool

    class Config:
        from_attributes = True


class ProductSpecificationResponse(BaseModel):
    spec_key: str
    spec_value: str

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=200)
    brand_id: int
    subcategory_id: int
    gender_id: Optional[int] = None
    base_price: Decimal = Field(..., gt=0)
    description: Optional[str] = None


class ProductCreate(ProductBase):
    supplier_id: Optional[int] = None
    is_featured: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    base_price: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


class ProductListResponse(BaseModel):
    """Lean response for product listing (grid view)"""
    id: int
    name: str
    slug: str
    base_price: Decimal
    is_featured: bool
    brand_name: Optional[str] = None
    category_name: Optional[str] = None
    primary_image_url: Optional[str] = None
    avg_rating: Optional[Decimal] = None
    review_count: int = 0
    total_available_stock: int = 0

    class Config:
        from_attributes = True


class ProductDetailResponse(ProductBase):
    """Full response for product detail page"""
    id: int
    is_active: bool
    is_featured: bool
    brand: Optional[BrandResponse] = None
    subcategory: Optional[SubCategoryResponse] = None
    images: List[ProductImageResponse] = []
    specifications: List[ProductSpecificationResponse] = []
    variant_count: int = 0

    class Config:
        from_attributes = True


# ============================================================
# VARIANT SCHEMAS
# ============================================================

class VariantBase(BaseModel):
    product_id: int
    sku: str = Field(..., max_length=100)
    barcode: Optional[str] = None
    color_id: Optional[int] = None
    size_id: Optional[int] = None
    material_id: Optional[int] = None
    price_override: Optional[Decimal] = None


class VariantCreate(VariantBase):
    pass


class VariantResponse(VariantBase):
    id: int
    is_active: bool
    color_name: Optional[str] = None
    size_name: Optional[str] = None
    material_name: Optional[str] = None
    available_stock: int = 0

    class Config:
        from_attributes = True


# ============================================================
# INVENTORY SCHEMAS
# ============================================================

class InventoryResponse(BaseModel):
    id: int
    variant_id: int
    warehouse_id: int
    warehouse_name: Optional[str] = None
    sku: Optional[str] = None
    current_stock: int
    reserved_stock: int
    available_stock: int
    reorder_level: int
    stock_status: str

    class Config:
        from_attributes = True


class InventoryAdjustRequest(BaseModel):
    quantity: int = Field(..., description="Positive to add, negative to subtract")
    movement_type: str = Field(default="adjustment")
    notes: Optional[str] = None
