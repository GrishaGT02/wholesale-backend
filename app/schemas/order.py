from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.order import OrderStatus


class OrderBase(BaseModel):
    title: str
    product_name: str  # Наименование товара
    delivery_volume: Optional[str] = None  # Объем поставки
    purchase_budget: Optional[float] = Field(None, gt=0, description="Бюджет закупки")
    product_description: Optional[str] = None  # Описание товара
    supplier_id: Optional[int] = None  # Может быть NULL до отклика поставщика
    deadline_at: datetime  # Сроки доставки
    cost: float = Field(gt=0, description="Стоимость должна быть больше 0")
    note: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    title: Optional[str] = None
    product_name: Optional[str] = None
    delivery_volume: Optional[str] = None
    purchase_budget: Optional[float] = Field(None, gt=0)
    product_description: Optional[str] = None
    supplier_id: Optional[int] = None
    deadline_at: Optional[datetime] = None
    cost: Optional[float] = Field(None, gt=0)
    note: Optional[str] = None
    status: Optional[OrderStatus] = None


class BuyerInfo(BaseModel):
    id: int
    username: str
    email: Optional[str] = None  # Email может быть None для покупателей

    class Config:
        from_attributes = True


class SupplierInfo(BaseModel):
    id: int
    name: str
    user_id: Optional[int] = None  # ID пользователя-поставщика для переписки

    class Config:
        from_attributes = True


class OrderResponse(OrderBase):
    id: int
    buyer_id: int
    buyer: Optional[BuyerInfo] = None
    supplier: Optional[SupplierInfo] = None
    ordered_at: datetime
    status: OrderStatus
    remaining_time: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Order(OrderResponse):
    pass

