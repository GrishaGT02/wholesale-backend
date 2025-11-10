from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserNotificationSettings, UserUpdate
from app.services import user_service

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить список пользователей (только для админов)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут просматривать список пользователей"
        )
    
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить пользователя по ID"""
    # Пользователь может видеть только свой профиль, админ - любой
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этого профиля"
        )
    
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user


@router.put("/me/notifications", response_model=UserResponse)
def update_notification_settings(
    settings: UserNotificationSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Обновить настройки уведомлений текущего пользователя"""
    current_user.email_notifications = settings.email_notifications
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Обновить профиль текущего пользователя"""
    from app.models.user import UserRole
    
    # Проверяем уникальность email, если он изменяется
    if user_update.email and user_update.email != current_user.email:
        existing_user = user_service.get_user_by_email(db, user_update.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
    
    # Проверяем уникальность username, если он изменяется
    if user_update.username and user_update.username != current_user.username:
        existing_user = user_service.get_user_by_username(db, user_update.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким username уже существует"
            )
    
    # Email обязателен для поставщиков
    if current_user.role == UserRole.SUPPLIER:
        final_email = user_update.email if user_update.email is not None else current_user.email
        if not final_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email обязателен для поставщиков"
            )
    
    # Обновляем поля
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.username is not None:
        current_user.username = user_update.username
    if user_update.organization_name is not None:
        current_user.organization_name = user_update.organization_name
    if user_update.inn is not None:
        current_user.inn = user_update.inn
    
    db.commit()
    db.refresh(current_user)
    return current_user

