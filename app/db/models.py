from sqlalchemy import Column, String, Float, Text, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    rating = Column(Float, default=0.0)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    img_url = Column(String(500), nullable=True)

class ProductOrder(Base):
    __tablename__ = "product_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product = Column(String(500), nullable=False)
    description = Column(String(1000), nullable=True)
    full_name = Column(String(500), nullable=False)
    phone = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    email = Column(String(500), nullable=True)
    address = Column(String(1000), nullable=False)
    city = Column(String(255), nullable=False)
    state = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    pin_code = Column(String(20), nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    is_cancelled = Column(Boolean, default=False)
    is_returned = Column(Boolean, default=False)

    tracking = relationship("OrderTracking", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderTracking(Base):
    __tablename__ = "order_tracking"

    id = Column(UUID(as_uuid=True), ForeignKey("product_orders.id", ondelete="CASCADE"), primary_key=True)
    current_location = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    progress_percentage = Column(Integer, nullable=False, default=0)

    order = relationship("ProductOrder", back_populates="tracking")
