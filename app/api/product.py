from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db, SessionLocal
from app.db.models import Product, ProductOrder, OrderTracking
from app.schema.product import ProductResponse, ProductCreate, BuyProductCreate, BuyProductResponse
from app.api.tracking import ROUTE

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db), skip: int = 0, limit: int = 10):
    """Get all products with pagination"""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    """Get a single product by its UUID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/buy_product/", response_model=BuyProductResponse)
def buy_product(buy_product: BuyProductCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new order and initialize tracking."""
    order = ProductOrder(**buy_product.dict())
    db.add(order)
    db.flush()

    tracking = OrderTracking(
        id=order.id,
        current_location=ROUTE[0],
        status="order_placed",
        progress_percentage=0,
        updated_at=datetime.utcnow(),
    )
    db.add(tracking)
    db.commit()
    db.refresh(order)

    background_tasks.add_task(_advance_tracking_background, order.id)

    return order


def _advance_tracking_background(order_id: UUID, interval_minutes: int = 1) -> None:
    """Advance tracking for an order periodically.

    Opens its own DB sessions to avoid using the request-scoped session.
    """
    try:
        for step_index, location in enumerate(ROUTE):
            db = SessionLocal()
            try:
                # stop advancing if order is cancelled/returned
                order = db.query(ProductOrder).filter(ProductOrder.id == order_id).first()
                if order is None or getattr(order, "is_cancelled", False) or getattr(order, "is_returned", False):
                    return

                tracking = db.query(OrderTracking).filter(OrderTracking.id == order_id).first()
                if tracking is None:
                    return

                tracking.current_location = location
                is_last = step_index == len(ROUTE) - 1
                tracking.status = "delivered" if is_last else ("in_transit" if step_index > 0 else "order_placed")
                tracking.progress_percentage = int((step_index / (len(ROUTE) - 1)) * 100)
                tracking.updated_at = datetime.utcnow()
                db.add(tracking)
                db.commit()
            finally:
                db.close()

            # sleep after committing this step except after the final step
            if step_index < len(ROUTE) - 1:
                import time
                time.sleep(per_transition_seconds)
    except Exception:
        # In production, log the error to your logging system
        pass


class OrderIdPayload(BaseModel):
    id: UUID


@router.post("/cancel_order/")
def cancel_order(payload: OrderIdPayload, db: Session = Depends(get_db)):
    order = db.query(ProductOrder).filter(ProductOrder.id == payload.id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.is_cancelled:
        return {"id": str(order.id), "is_cancelled": True, "is_returned": order.is_returned}
    # Only allow cancel when tracking is still at order_placed
    tracking = db.query(OrderTracking).filter(OrderTracking.id == order.id).first()
    if tracking is None:
        raise HTTPException(status_code=404, detail="Tracking not found for order")
    if tracking.status not in ("order_placed",):
        raise HTTPException(status_code=400, detail="Order cannot be cancelled after processing has started")
    order.is_cancelled = True
    # Optionally mark tracking as cancelled and 0% progress
    tracking.status = "cancelled"
    tracking.progress_percentage = 0
    db.add(order)
    db.add(tracking)
    db.commit()
    return {"id": str(order.id), "is_cancelled": order.is_cancelled, "is_returned": order.is_returned}


@router.post("/return_order/")
def return_order(payload: OrderIdPayload, db: Session = Depends(get_db)):
    order = db.query(ProductOrder).filter(ProductOrder.id == payload.id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.is_returned:
        return {"id": str(order.id), "is_cancelled": order.is_cancelled, "is_returned": True}
    tracking = db.query(OrderTracking).filter(OrderTracking.id == order.id).first()
    if tracking is None:
        raise HTTPException(status_code=404, detail="Tracking not found for order")
    # Only allow return when delivered
    if tracking.status != "delivered":
        raise HTTPException(status_code=400, detail="Order can be returned only after delivery")
    order.is_returned = True
    tracking.status = "returned"
    db.add(order)
    db.add(tracking)
    db.commit()
    return {"id": str(order.id), "is_cancelled": order.is_cancelled, "is_returned": order.is_returned}

    
