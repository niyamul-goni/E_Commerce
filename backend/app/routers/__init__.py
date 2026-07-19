from app.routers.auth import router as auth_router
from app.routers.catalog import (
    categories_router,
    collections_router,
    customers_router,
    products_router,
    subcategories_router,
    suppliers_router,
)
from app.routers.commerce import (
    addresses_router,
    cart_items_router,
    coupon_validate_router,
    dashboard_router,
    order_items_router,
    orders_router,
    payments_router,
    profile_router,
    reviews_router,
    shipments_router,
    wishlist_router,
)

__all__ = [
    "addresses_router",
    "auth_router",
    "cart_items_router",
    "categories_router",
    "collections_router",
    "coupon_validate_router",
    "customers_router",
    "dashboard_router",
    "order_items_router",
    "orders_router",
    "payments_router",
    "products_router",
    "profile_router",
    "reviews_router",
    "shipments_router",
    "subcategories_router",
    "suppliers_router",
    "wishlist_router",
]
