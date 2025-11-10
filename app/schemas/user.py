from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    email: Optional[str] = None  # Обязателен только для поставщиков
    username: str
    role: UserRole = UserRole.BUYER
    organization_name: Optional[str] = None  # Название организации или ФИО для ИП
    inn: Optional[str] = None  # ИНН
    email_notifications: bool = True  # Получать уведомления на email


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: int
    password_hash: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    email_notifications: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserResponse):
    pass


class UserNotificationSettings(BaseModel):
    email_notifications: bool


class UserUpdate(BaseModel):
    """Схема для обновления профиля пользователя"""
    email: Optional[str] = None
    username: Optional[str] = None
    organization_name: Optional[str] = None
    inn: Optional[str] = None


class UserUpdateResponse(UserResponse):
    """Схема ответа при обновлении профиля - может содержать новый токен"""
    access_token: Optional[str] = None

