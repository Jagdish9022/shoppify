from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    rating: Optional[float] = 0.0
    price: float
    quantity: Optional[int] = 0
    img_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

class BuyProductBase(BaseModel):
    product_id: Optional[uuid.UUID] = None
    product: str
    description: Optional[str] = None
    full_name: str
    phone: str
    quantity: int = 1
    email: Optional[str] = None
    address: str
    city: str
    state: str
    country: str
    pin_code: str
    price: float
    is_cancelled: bool = False
    is_returned: bool = False

class BuyProductCreate(BuyProductBase):
    pass

class BuyProductResponse(BuyProductBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

class TrackingResponse(BaseModel):
    id: uuid.UUID
    current_location: str
    status: str
    updated_at: datetime
    progress_percentage: int
    next_location: Optional[str] = None

    class Config:
        from_attributes = True

class PhoneNumberRequest(BaseModel):
    phone: str

class OrderByPhoneResponse(BaseModel):
    order_id: uuid.UUID
    product_id: Optional[uuid.UUID]

    class Config:
        from_attributes = True

class OrdersByPhoneResponse(BaseModel):
    phone: str
    total_orders: int
    orders: List[OrderByPhoneResponse]

class ReasonPayload(BaseModel):
    id: uuid.UUID
    reason: str