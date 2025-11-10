from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.core.database import Base


class OrderStatus(str, enum.Enum):
    IN_PROGRESS = "в_работе"
    COMPLETED = "завершен"
    CANCELLED = "отменен"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    product_name = Column(String, nullable=False)  # Наименование товара
    delivery_volume = Column(String, nullable=True)  # Объем поставки (может быть строка, например "1000 шт")
    purchase_budget = Column(Float, nullable=True)  # Бюджет закупки
    product_description = Column(Text, nullable=True)  # Описание товара
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)  # Может быть NULL до отклика поставщика
    ordered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deadline_at = Column(DateTime, nullable=False)  # Сроки доставки
    cost = Column(Float, nullable=False)
    note = Column(Text)
    status = Column(Enum(OrderStatus), default=OrderStatus.IN_PROGRESS, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    buyer = relationship("User", back_populates="orders", foreign_keys=[buyer_id])
    supplier = relationship("Supplier", back_populates="orders")
    messages = relationship("Message", back_populates="order")

