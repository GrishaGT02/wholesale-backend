from pydantic import BaseModel
from typing import Optional


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None


class ProductCreate(ProductBase):
    supplier_id: int


class ProductResponse(ProductBase):
    id: int
    supplier_id: int

    class Config:
        from_attributes = True


class Product(ProductResponse):
    pass

