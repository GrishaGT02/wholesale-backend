from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    BUYER = "buyer"
    SUPPLIER = "supplier"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)  # Обязателен только для поставщиков
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.BUYER, nullable=False)
    organization_name = Column(String, nullable=True)  # Название организации или ФИО для ИП
    inn = Column(String, nullable=True)  # ИНН
    email_notifications = Column(Boolean, default=True, nullable=False)  # Получать уведомления на email
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")

