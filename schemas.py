from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# =====================================
# USER
# =====================================

class UserCreate(BaseModel):

    name: str = Field(
        ...,
        min_length=3,
        max_length=100
    )

    email: EmailStr


class UserResponse(BaseModel):

    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================
# PRODUCT
# =====================================

class ProductCreate(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    description: Optional[str] = None

    price: float = Field(
        ...,
        gt=0
    )

    inventory: int = Field(
        ...,
        ge=0
    )


class ProductResponse(BaseModel):

    id: int
    name: str
    description: Optional[str]
    price: float
    inventory: int
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):

    inventory: int = Field(
        ...,
        ge=0
    )


# =====================================
# ORDER ITEM
# =====================================

class OrderItemCreate(BaseModel):

    product_id: int = Field(
        ...,
        gt=0
    )

    quantity: int = Field(
        ...,
        gt=0
    )


class OrderItemResponse(BaseModel):

    id: int
    product_id: int
    quantity: int
    unit_price: float
    item_total: float

    class Config:
        from_attributes = True


# =====================================
# ORDER
# =====================================

class OrderCreate(BaseModel):

    user_id: int = Field(
        ...,
        gt=0
    )

    items: List[OrderItemCreate]


class OrderResponse(BaseModel):

    id: int
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True