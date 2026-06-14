from app.routers.auth import router as auth_router
from app.routers.catalog import categories_router, customers_router, products_router, suppliers_router
from app.routers.commerce import (
    cart_items_router,
    dashboard_router,
    order_items_router,
    orders_router,
    payments_router,
    reviews_router,
    shipments_router,
)

__all__ = [
    "auth_router",
    "categories_router",
    "cart_items_router",
    "customers_router",
    "dashboard_router",
    "order_items_router",
    "orders_router",
    "payments_router",
    "products_router",
    "reviews_router",
    "shipments_router",
    "suppliers_router",
]
