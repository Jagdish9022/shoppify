from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db, SessionLocal
from app.db.models import Product, ProductOrder, OrderTracking, OrderReason
from app.schema.product import ProductResponse, ProductCreate, BuyProductCreate, BuyProductResponse, PhoneNumberRequest, OrdersByPhoneResponse, OrderByPhoneResponse, ReasonPayload
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
    # If product_id is provided, validate it exists
    if buy_product.product_id:
        product = db.query(Product).filter(Product.id == buy_product.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    
    # Exclude 'reason' from creation payload; it's only used on cancel
    payload = buy_product.dict(exclude={"reason"}, exclude_none=True)
    order = ProductOrder(**payload)
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

    background_tasks.add_task(_advance_tracking_background, order.id, 12)

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
                time.sleep(int(max(1, interval_minutes * 60)))
    except Exception:
        # In production, log the error to your logging system
        pass


class OrderIdPayload(BaseModel):
    id: UUID

class CancelOrderPayload(BaseModel):
    id: UUID
    reason: str


@router.post("/cancel_order/")
def cancel_order(payload: ReasonPayload, db: Session = Depends(get_db)):
    order = db.query(ProductOrder).filter(ProductOrder.id == payload.id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.is_cancelled:
        # Get latest cancel reason if exists
        existing_reason = (
            db.query(OrderReason)
            .filter(OrderReason.order_id == order.id, OrderReason.is_cancelled == True)
            .order_by(OrderReason.created_at.desc())
            .first()
        )
        return {
            "id": str(order.id),
            "is_cancelled": True,
            "is_returned": order.is_returned,
            "reason": getattr(existing_reason, "reason", None),
        }
    # Only allow cancel when tracking is still at order_placed
    tracking = db.query(OrderTracking).filter(OrderTracking.id == order.id).first()
    if tracking is None:
        raise HTTPException(status_code=404, detail="Tracking not found for order")
    if tracking.status not in ("order_placed",):
        raise HTTPException(status_code=400, detail="Order cannot be cancelled after processing has started")

    order.is_cancelled = True
    tracking.status = "cancelled"
    tracking.progress_percentage = 0

    reason_entry = OrderReason(
        order_id=order.id,
        is_cancelled=True,
        is_returned=False,
        reason=payload.reason,
    )

    db.add(order)
    db.add(tracking)
    db.add(reason_entry)
    db.commit()
    return {
        "id": str(order.id),
        "is_cancelled": order.is_cancelled,
        "is_returned": order.is_returned,
        "reason": payload.reason,
    }


class ProductIdsRequest(BaseModel):
    ids: List[UUID]


@router.post("/by_ids", response_model=List[ProductResponse])
def post_products_by_ids(payload: ProductIdsRequest, db: Session = Depends(get_db)):
    """Get products by an array of UUIDs via POST body and return an array.

    Example body: { "ids": ["uuid1", "uuid2"] }
    """
    if not payload.ids:
        raise HTTPException(status_code=400, detail="Body must include non-empty 'ids' array")

    products = db.query(Product).filter(Product.id.in_(payload.ids)).all()
    return products

@router.post("/return_order/")
def return_order(payload: ReasonPayload, db: Session = Depends(get_db)):
    order = db.query(ProductOrder).filter(ProductOrder.id == payload.id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.is_cancelled:
        raise HTTPException(status_code=400, detail="Order is already cancelled")
    if order.is_returned:
        # Get latest return reason if exists
        existing_reason = (
            db.query(OrderReason)
            .filter(OrderReason.order_id == order.id, OrderReason.is_returned == True)
            .order_by(OrderReason.created_at.desc())
            .first()
        )
        return {
            "id": str(order.id),
            "is_cancelled": order.is_cancelled,
            "is_returned": True,
            "reason": getattr(existing_reason, "reason", None),
        }
    tracking = db.query(OrderTracking).filter(OrderTracking.id == order.id).first()
    if tracking is None:
        raise HTTPException(status_code=404, detail="Tracking not found for order")
    # Only allow return when delivered
    if tracking.status != "delivered":
        raise HTTPException(status_code=400, detail="Order can be returned only after delivery")

    order.is_returned = True
    tracking.status = "returned"

    reason_entry = OrderReason(
        order_id=order.id,
        is_cancelled=False,
        is_returned=True,
        reason=payload.reason,
    )

    db.add(order)
    db.add(tracking)
    db.add(reason_entry)
    db.commit()
    return {
        "id": str(order.id),
        "is_cancelled": order.is_cancelled,
        "is_returned": order.is_returned,
        "reason": payload.reason,
    }

@router.post("/orders_by_phone/", response_model=OrdersByPhoneResponse)
def get_orders_by_phone(payload: PhoneNumberRequest, db: Session = Depends(get_db)):
    """Get all orders by phone number"""
    
    # Query all orders with the given phone number
    orders = db.query(ProductOrder).filter(ProductOrder.phone == payload.phone).all()
    
    if not orders:
        raise HTTPException(
            status_code=404, 
            detail=f"No orders found for phone number: {payload.phone}"
        )
    
    # Convert orders to response format
    order_responses = []
    for order in orders:
        order_response = OrderByPhoneResponse(
            order_id=order.id,
            product_id=order.product_id
        )
        order_responses.append(order_response)
    
    return OrdersByPhoneResponse(
        phone=payload.phone,
        total_orders=len(orders),
        orders=order_responses
    )

    
