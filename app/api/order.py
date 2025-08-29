from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Order, OrderStatus, Product
from app.schema.product import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order"""
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == order_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if product has sufficient quantity
    if product.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is out of stock"
        )
    
    # Create order
    order = Order(
        product_id=order_data.product_id,
        user_id=order_data.user_id,
        status=OrderStatus.PENDING
    )
    
    # Reduce product quantity
    product.quantity -= 1
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get order by ID"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order

@router.get("/", response_model=List[OrderResponse])
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all orders with pagination"""
    
    orders = db.query(Order).offset(skip).limit(limit).all()
    return orders

@router.put("/{order_id}/status")
def update_order_status(
    order_id: str, 
    status: OrderStatus, 
    db: Session = Depends(get_db)
):
    """Update order status"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order.status = status
    db.commit()
    db.refresh(order)
    
    return {"message": f"Order status updated to {status.value}", "order": order}
