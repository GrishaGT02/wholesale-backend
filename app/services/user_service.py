from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Получить пользователя по email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Получить пользователя по username"""
    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Получить список пользователей"""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Создать нового пользователя"""
    # Проверка на существование
    if user.email and get_user_by_email(db, user.email):
        raise ValueError("Пользователь с таким email уже существует")
    if get_user_by_username(db, user.username):
        raise ValueError("Пользователь с таким username уже существует")
    
    # Email обязателен для поставщиков
    from app.models.user import UserRole
    if user.role == UserRole.SUPPLIER and not user.email:
        raise ValueError("Email обязателен для поставщиков")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=hashed_password,
        role=user.role,
        organization_name=user.organization_name,
        inn=user.inn,
        email_notifications=user.email_notifications if hasattr(user, 'email_notifications') else True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Если поставщик, создаем запись в suppliers
    if user.role == UserRole.SUPPLIER:
        from app.models.supplier import Supplier
        supplier = Supplier(
            name=user.organization_name or user.username,
            user_id=db_user.id,
            contact_info=user.email
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
    
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Аутентификация пользователя"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

