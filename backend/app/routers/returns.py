"""
FashionHub — Returns & Refunds Router
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sales import ReturnRequest, Refund
from app.schemas.order import (
    ReturnRequestCreate, ReturnRequestResponse,
    RefundCreate, RefundResponse,
)

router = APIRouter(prefix="/returns", tags=["Returns & Refunds"])


@router.get("/", response_model=list[ReturnRequestResponse])
def list_returns(
    status: str = None,
    db: Session = Depends(get_db)
):
    q = db.query(ReturnRequest)
    if status:
        q = q.filter(ReturnRequest.status == status)
    return q.order_by(ReturnRequest.id.desc()).limit(50).all()


@router.post("/", response_model=ReturnRequestResponse, status_code=201)
def create_return_request(payload: ReturnRequestCreate, db: Session = Depends(get_db)):
    rr = ReturnRequest(**payload.model_dump())
    db.add(rr)
    db.commit()
    db.refresh(rr)
    return rr


@router.put("/{return_id}/approve")
def approve_return(return_id: int, db: Session = Depends(get_db)):
    """
    Approve a return request.
    Trigger fn_restore_inventory_on_return fires and restores stock automatically.
    """
    rr = db.query(ReturnRequest).get(return_id)
    if not rr:
        raise HTTPException(404, detail="Return request not found")
    if rr.status != "pending":
        raise HTTPException(409, detail=f"Cannot approve return with status: {rr.status}")
    rr.status = "approved"
    db.commit()
    db.refresh(rr)
    return {"message": "Return approved. Inventory restored by database trigger.", "return_id": return_id}


@router.put("/{return_id}/reject")
def reject_return(return_id: int, notes: str = None, db: Session = Depends(get_db)):
    rr = db.query(ReturnRequest).get(return_id)
    if not rr:
        raise HTTPException(404, detail="Return request not found")
    rr.status = "rejected"
    if notes:
        rr.notes = notes
    db.commit()
    return {"message": "Return rejected", "return_id": return_id}


@router.post("/refunds", response_model=RefundResponse, status_code=201)
def create_refund(payload: RefundCreate, db: Session = Depends(get_db)):
    refund = Refund(**payload.model_dump())
    db.add(refund)
    db.commit()
    db.refresh(refund)
    return refund
