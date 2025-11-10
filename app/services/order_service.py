from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate
from app.services import supplier_service, user_service


def calculate_remaining_time(deadline: datetime) -> Optional[str]:
    """Расчет оставшегося времени до дедлайна в формате 'X д. Y ч.'"""
    now = datetime.utcnow()
    if deadline < now:
        return "Просрочен"
    
    delta = deadline - now
    days = delta.days
    hours = delta.seconds // 3600
    
    if days > 0:
        return f"{days} д. {hours} ч."
    elif hours > 0:
        return f"{hours} ч."
    else:
        minutes = delta.seconds // 60
        return f"{minutes} мин."


def get_order(db: Session, order_id: int) -> Optional[Order]:
    """Получить заказ по ID"""
    return db.query(Order).filter(Order.id == order_id).first()


def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    buyer_id: Optional[int] = None
) -> List[Order]:
    """Получить список заказов с фильтрами"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    if buyer_id:
        query = query.filter(Order.buyer_id == buyer_id)
    
    return query.offset(skip).limit(limit).all()


def create_order(db: Session, order: OrderCreate, buyer_id: int) -> Order:
    """Создать новый заказ"""
    # Проверка существования поставщика (если указан)
    if order.supplier_id:
        supplier = supplier_service.get_supplier(db, order.supplier_id)
        if not supplier:
            raise ValueError(f"Поставщик с ID {order.supplier_id} не найден")
    
    db_order = Order(
        **order.dict(),
        buyer_id=buyer_id
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Email уведомления теперь отправляются в endpoint через BackgroundTasks
    # Это позволяет не блокировать создание заказа
    
    return db_order




def update_order(db: Session, order_id: int, order_update: OrderUpdate) -> Optional[Order]:
    """Обновить заказ"""
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    update_data = order_update.dict(exclude_unset=True)
    
    # Проверка поставщика если он изменяется
    if "supplier_id" in update_data:
        supplier = supplier_service.get_supplier(db, update_data["supplier_id"])
        if not supplier:
            raise ValueError(f"Поставщик с ID {update_data['supplier_id']} не найден")
    
    for field, value in update_data.items():
        setattr(db_order, field, value)
    
    db_order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    return db_order


def delete_order(db: Session, order_id: int) -> bool:
    """Удалить заказ"""
    db_order = get_order(db, order_id)
    if not db_order:
        return False
    
    db.delete(db_order)
    db.commit()
    return True


def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Optional[Order]:
    """Обновить статус заказа"""
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    db_order.status = status
    db_order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    return db_order

