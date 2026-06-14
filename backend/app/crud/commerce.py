from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.cart_item import CartItem
from app.models.category import Category
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.product import Product
from app.models.review import Review
from app.models.supplier import Supplier
from app.models.shipment import Shipment
from app.schemas.entities import (
    CartItemCreate,
    CartItemUpdate,
    OrderCreate,
    OrderItemCreate,
    OrderStatusUpdate,
    PaymentCreate,
    ReviewCreate,
    ShipmentCreate,
)
from app.utils.generators import generate_order_number


def create_order(db: Session, order_in: OrderCreate) -> Order:
    order = Order(
        order_number=generate_order_number(),
        customer_id=order_in.customer_id,
        status="pending",
        total_amount=Decimal("0.00"),
        shipping_address=order_in.shipping_address,
        billing_address=order_in.billing_address,
    )
    db.add(order)
    db.flush()

    total_amount = Decimal("0.00")
    for item_in in order_in.items:
        item = add_order_item(db, order.id, item_in)
        total_amount += item.line_total

    order.total_amount = total_amount
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def add_order_item(db: Session, order_id: int, item_in: OrderItemCreate) -> OrderItem:
    order = db.get(Order, order_id)
    product = db.get(Product, item_in.product_id)
    if order is None or product is None:
        raise ValueError("Order or product not found")
    if product.stock_quantity < item_in.quantity:
        raise ValueError("Insufficient stock")

    existing_item = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order_id, OrderItem.product_id == item_in.product_id)
        .first()
    )
    if existing_item is not None:
        raise ValueError("Product already exists in order")

    unit_price = Decimal(product.price)
    line_total = unit_price * item_in.quantity
    order_item = OrderItem(
        order_id=order_id,
        product_id=item_in.product_id,
        quantity=item_in.quantity,
        unit_price=unit_price,
        line_total=line_total,
    )
    product.stock_quantity -= item_in.quantity
    db.add(order_item)
    db.add(product)
    db.flush()
    return order_item


def remove_order_item(db: Session, order_id: int, order_item_id: int) -> Optional[OrderItem]:
    order_item = (
        db.query(OrderItem)
        .filter(OrderItem.id == order_item_id, OrderItem.order_id == order_id)
        .first()
    )
    if order_item is None:
        return None

    product = db.get(Product, order_item.product_id)
    if product is not None:
        product.stock_quantity += order_item.quantity
        db.add(product)
    db.delete(order_item)
    db.commit()
    return order_item


def update_order_status(db: Session, order: Order, status: str) -> Order:
    order.status = status
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def record_payment(db: Session, payment_in: PaymentCreate) -> Payment:
    payment = Payment(
        order_id=payment_in.order_id,
        amount=payment_in.amount,
        payment_method=payment_in.payment_method,
        payment_status=payment_in.payment_status.value,
        transaction_reference=payment_in.transaction_reference,
    )
    db.add(payment)
    order = db.get(Order, payment_in.order_id)
    if order is None:
        raise ValueError("Order not found")
    if payment.payment_status == "completed":
        order.status = "paid"
    db.add(order)
    db.commit()
    db.refresh(payment)
    return payment


def create_shipment(db: Session, shipment_in: ShipmentCreate) -> Shipment:
    shipment = Shipment(
        order_id=shipment_in.order_id,
        carrier=shipment_in.carrier,
        tracking_number=shipment_in.tracking_number,
        shipment_status=shipment_in.shipment_status.value,
    )
    db.add(shipment)
    order = db.get(Order, shipment_in.order_id)
    if order is None:
        raise ValueError("Order not found")
    order.status = "shipped" if shipment.shipment_status == "in_transit" else order.status
    db.add(order)
    db.commit()
    db.refresh(shipment)
    return shipment


def add_review(db: Session, review_in: ReviewCreate) -> Review:
    review = Review(
        customer_id=review_in.customer_id,
        product_id=review_in.product_id,
        rating=review_in.rating,
        comment=review_in.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def upsert_cart_item(db: Session, cart_item_in: CartItemCreate) -> CartItem:
    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.customer_id == cart_item_in.customer_id,
            CartItem.product_id == cart_item_in.product_id,
        )
        .first()
    )
    if cart_item is None:
        cart_item = CartItem(
            customer_id=cart_item_in.customer_id,
            product_id=cart_item_in.product_id,
            quantity=cart_item_in.quantity,
        )
        db.add(cart_item)
    else:
        cart_item.quantity += cart_item_in.quantity
        db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def update_cart_item_quantity(db: Session, cart_item: CartItem, cart_item_in: CartItemUpdate) -> CartItem:
    cart_item.quantity = cart_item_in.quantity
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def remove_cart_item(db: Session, cart_item: CartItem) -> None:
    db.delete(cart_item)
    db.commit()


def get_order_history(db: Session, customer_id: int) -> list[Order]:
    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.customer_id == customer_id)
        .order_by(Order.order_date.desc())
        .all()
    )


def get_all_orders(db: Session) -> list[Order]:
    return db.query(Order).options(selectinload(Order.items)).order_by(Order.order_date.desc()).all()


def get_dashboard_counts(db: Session) -> dict[str, Decimal | int]:
    total_sales = db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or Decimal("0.00")
    average_order_value = db.query(func.coalesce(func.avg(Order.total_amount), 0)).scalar() or Decimal("0.00")
    return {
        "total_customers": db.query(func.count()).select_from(Customer).scalar() or 0,
        "total_categories": db.query(func.count()).select_from(Category).scalar() or 0,
        "total_suppliers": db.query(func.count()).select_from(Supplier).scalar() or 0,
        "total_products": db.query(func.count()).select_from(Product).scalar() or 0,
        "total_orders": db.query(func.count()).select_from(Order).scalar() or 0,
        "total_sales": total_sales,
        "total_payments": db.query(func.coalesce(func.sum(Payment.amount), 0)).scalar() or Decimal("0.00"),
        "total_cart_items": db.query(func.coalesce(func.sum(CartItem.quantity), 0)).scalar() or 0,
        "average_order_value": average_order_value,
        "low_stock_products": db.query(func.count()).select_from(Product).filter(Product.stock_quantity < 10).scalar() or 0,
        "top_rated_products": db.query(func.count()).select_from(Review).filter(Review.rating >= 4).scalar() or 0,
        "pending_orders": db.query(func.count()).select_from(Order).filter(Order.status == "pending").scalar() or 0,
        "shipped_orders": db.query(func.count()).select_from(Order).filter(Order.status == "shipped").scalar() or 0,
    }
