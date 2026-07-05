"""
FashionHub — Inventory Router
Endpoints: GET inventory status, adjust stock, low stock alerts
Uses PostgreSQL views for rich data responses
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import Inventory, InventoryMovement
from app.schemas.product import InventoryResponse, InventoryAdjustRequest

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/", response_model=List[dict])
def list_inventory(
    warehouse_id: Optional[int] = Query(None),
    low_stock_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Returns inventory status per (variant, warehouse).
    Uses inventory_status_view for enriched data.
    """
    sql = text("""
        SELECT *
        FROM inventory_status_view
        WHERE (:wh IS NULL OR warehouse_id = :wh)
          AND (NOT :low OR stock_status IN ('Low Stock', 'Out of Stock'))
        ORDER BY stock_status, days_of_stock_remaining NULLS LAST
        LIMIT 200
    """)
    rows = db.execute(sql, {"wh": warehouse_id, "low": low_stock_only}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/low-stock", response_model=List[dict])
def get_low_stock_items(db: Session = Depends(get_db)):
    """Items at or below reorder level — includes supplier contact for procurement."""
    rows = db.execute(text("SELECT * FROM low_stock_products_view LIMIT 100")).mappings().all()
    return [dict(r) for r in rows]


@router.get("/warehouse-summary", response_model=List[dict])
def warehouse_inventory_summary(db: Session = Depends(get_db)):
    """Per-warehouse stock summary with capacity utilization."""
    rows = db.execute(text("SELECT * FROM warehouse_inventory_view")).mappings().all()
    return [dict(r) for r in rows]


@router.get("/health", response_model=List[dict])
def inventory_health_snapshot(db: Session = Depends(get_db)):
    """Pre-computed inventory health from materialized view (fast)."""
    rows = db.execute(text(
        "SELECT * FROM mat_inventory_health ORDER BY total_available_stock ASC LIMIT 100"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.post("/{inventory_id}/adjust", status_code=200)
def adjust_inventory(
    inventory_id: int,
    payload: InventoryAdjustRequest,
    db: Session = Depends(get_db),
):
    """
    Adjust inventory stock. Creates an inventory_movement record.
    Trigger fn_prevent_negative_stock will raise if stock goes below 0.
    """
    inv = db.query(Inventory).get(inventory_id)
    if not inv:
        raise HTTPException(404, detail="Inventory record not found")

    try:
        # Update stock
        inv.current_stock = inv.current_stock + payload.quantity

        # Record movement
        movement = InventoryMovement(
            inventory_id=inventory_id,
            movement_type=payload.movement_type,
            quantity=payload.quantity,
            notes=payload.notes,
        )
        db.add(movement)
        db.commit()
        db.refresh(inv)

        return {
            "message": "Stock adjusted successfully",
            "inventory_id": inventory_id,
            "new_current_stock": inv.current_stock,
            "quantity_adjusted": payload.quantity,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(422, detail=str(e))


@router.get("/{inventory_id}/movements")
def inventory_movement_history(inventory_id: int, db: Session = Depends(get_db)):
    """Full movement history for an inventory record (audit trail)."""
    movements = (
        db.query(InventoryMovement)
        .filter(InventoryMovement.inventory_id == inventory_id)
        .order_by(InventoryMovement.id.desc())
        .limit(50)
        .all()
    )
    return movements
