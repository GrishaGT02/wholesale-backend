from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SupplierBase(BaseModel):
    name: str
    contact_info: Optional[str] = None
    country: str = "China"
    rating: float = 0.0


class SupplierCreate(SupplierBase):
    pass


class SupplierResponse(SupplierBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Supplier(SupplierResponse):
    pass

