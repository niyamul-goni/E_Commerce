from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import get_current_user, require_admin
from app.crud.commerce import (
    add_order_item,
    add_review,
    get_all_orders,
    create_order,
    create_shipment,
    get_dashboard_counts,
    get_order_history,
    remove_cart_item,
    remove_order_item,
    record_payment,
    update_cart_item_quantity,
    update_order_status,
    upsert_cart_item,
)
from app.database import get_db
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.review import Review
from app.models.shipment import Shipment
from app.schemas import (
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    DashboardSummary,
    Message,
    OrderCreate,
    OrderItemCreate,
    OrderItemRead,
    OrderRead,
    OrderStatusUpdate,
    PaymentCreate,
    PaymentRead,
    ReviewCreate,
    ReviewRead,
    ShipmentCreate,
    ShipmentRead,
)

orders_router = APIRouter(prefix="/orders", tags=["orders"])
order_items_router = APIRouter(prefix="/orders", tags=["order-items"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])
shipments_router = APIRouter(prefix="/shipments", tags=["shipments"])
reviews_router = APIRouter(prefix="/reviews", tags=["reviews"])
cart_items_router = APIRouter(prefix="/cart-items", tags=["cart-items"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@orders_router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def place_order(order_in: OrderCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> Order:
    if not current_user.is_admin and order_in.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot place orders for another customer")
    try:
        return create_order(db, order_in)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@orders_router.get("/me", response_model=list[OrderRead])
def get_my_orders(db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> list[Order]:
    return get_order_history(db, current_user.id)


@orders_router.get("", response_model=list[OrderRead], dependencies=[Depends(require_admin)])
def list_all_orders(db: Session = Depends(get_db)) -> list[Order]:
    return get_all_orders(db)


@orders_router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> Order:
    order = db.query(Order).options(selectinload(Order.items)).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this order")
    return order


@orders_router.put("/{order_id}/status", response_model=OrderRead, dependencies=[Depends(require_admin)])
def change_order_status(order_id: int, status_in: OrderStatusUpdate, db: Session = Depends(get_db)) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return update_order_status(db, order, status_in.status.value)


@order_items_router.post("/{order_id}/items", response_model=OrderItemRead, status_code=status.HTTP_201_CREATED)
def add_item_to_order(order_id: int, item_in: OrderItemCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> OrderItem:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to modify this order")
    try:
        return add_order_item(db, order_id, item_in)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@order_items_router.delete("/{order_id}/items/{order_item_id}", response_model=Message)
def remove_item_from_order(order_id: int, order_item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> Message:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to modify this order")
    deleted = remove_order_item(db, order_id, order_item_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")
    return Message(message="Order item removed successfully")


@payments_router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(payment_in: PaymentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> Payment:
    order = db.get(Order, payment_in.order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to pay for this order")
    try:
        return record_payment(db, payment_in)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@payments_router.get("/order/{order_id}", response_model=PaymentRead)
def get_payment_by_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> Payment:
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this payment")
    return payment


@shipments_router.post("", response_model=ShipmentRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_shipment_endpoint(shipment_in: ShipmentCreate, db: Session = Depends(get_db)) -> Shipment:
    try:
        return create_shipment(db, shipment_in)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@shipments_router.get("/order/{order_id}", response_model=ShipmentRead)
def get_shipment_by_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> Shipment:
    shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this shipment")
    return shipment


@reviews_router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(review_in: ReviewCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> Review:
    if not current_user.is_admin and review_in.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot write reviews for another customer")
    try:
        return add_review(db, review_in)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create review") from exc


@reviews_router.get("/product/{product_id}", response_model=list[ReviewRead])
def list_reviews_for_product(product_id: int, db: Session = Depends(get_db)) -> list[Review]:
    return db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()


@cart_items_router.post("", response_model=CartItemRead, status_code=status.HTTP_201_CREATED)
def add_to_cart(cart_item_in: CartItemCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> CartItem:
    if not current_user.is_admin and cart_item_in.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another customer's cart")
    return upsert_cart_item(db, cart_item_in)


@cart_items_router.get("/me", response_model=list[CartItemRead])
def list_my_cart_items(db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> list[CartItem]:
    return db.query(CartItem).filter(CartItem.customer_id == current_user.id).order_by(CartItem.created_at.desc()).all()


@cart_items_router.put("/{cart_item_id}", response_model=CartItemRead)
def update_cart_item(cart_item_id: int, cart_item_in: CartItemUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> CartItem:
    cart_item = db.get(CartItem, cart_item_id)
    if cart_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    if not current_user.is_admin and cart_item.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another customer's cart")
    return update_cart_item_quantity(db, cart_item, cart_item_in)


@cart_items_router.delete("/{cart_item_id}", response_model=Message)
def delete_cart_item(cart_item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> Message:
    cart_item = db.get(CartItem, cart_item_id)
    if cart_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    if not current_user.is_admin and cart_item.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another customer's cart")
    remove_cart_item(db, cart_item)
    return Message(message="Cart item removed successfully")


@dashboard_router.get("/summary", response_model=DashboardSummary, dependencies=[Depends(require_admin)])
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    counts = get_dashboard_counts(db)
    return DashboardSummary(**counts)
