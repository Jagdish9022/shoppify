from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.db.models import OrderTracking, ProductOrder
from app.schema.product import TrackingResponse


router = APIRouter(prefix="/track", tags=["tracking"])

# fixed route sequence
ROUTE = ["Manmad", "Yeola", "Kopargaon", "Talegaon Dighe", "Sangamner", "Delivered"]


@router.get("/{order_id}", response_model=TrackingResponse)
def track_order(order_id: str, db: Session = Depends(get_db)):
    tracking = db.query(OrderTracking).filter(OrderTracking.id == order_id).first()
    if tracking is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # If order is cancelled or returned, do not track, return message instead
    order = db.query(ProductOrder).filter(ProductOrder.id == order_id).first()
    if order and (getattr(order, "is_cancelled", False) or getattr(order, "is_returned", False)):
        raise HTTPException(status_code=400, detail="This order is cancelled or returned and is not trackable")

    try:
        current_index = ROUTE.index(tracking.current_location)
    except ValueError:
        current_index = 0

    next_location: Optional[str] = ROUTE[current_index + 1] if current_index < len(ROUTE) - 1 else None

    return TrackingResponse(
        id=tracking.id,
        current_location=tracking.current_location,
        status=tracking.status,
        updated_at=tracking.updated_at,
        progress_percentage=tracking.progress_percentage,
        next_location=next_location,
    )
