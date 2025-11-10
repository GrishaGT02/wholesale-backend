from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.order import OrderStatus
from app.models.supplier import Supplier
from app.schemas.order import Order, OrderCreate, OrderUpdate, OrderResponse
from app.services import order_service

router = APIRouter()


def format_order_response(order, db: Session) -> OrderResponse:
    """Форматирование ответа с расчетом оставшегося времени"""
    from app.schemas.order import BuyerInfo, SupplierInfo
    
    order_dict = {
        "id": order.id,
        "title": order.title,
        "product_name": order.product_name,
        "delivery_volume": order.delivery_volume,
        "purchase_budget": order.purchase_budget,
        "product_description": order.product_description,
        "buyer_id": order.buyer_id,
        "supplier_id": order.supplier_id,
        "ordered_at": order.ordered_at,
        "deadline_at": order.deadline_at,
        "cost": order.cost,
        "note": order.note,
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "remaining_time": order_service.calculate_remaining_time(order.deadline_at),
        "buyer": BuyerInfo(
            id=order.buyer.id,
            username=order.buyer.username,
            email=order.buyer.email if order.buyer.email else None
        ) if order.buyer else None,
        "supplier": SupplierInfo(
            id=order.supplier.id,
            name=order.supplier.name,
            user_id=order.supplier.user_id
        ) if order.supplier else None
    }
    return OrderResponse(**order_dict)


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить список заказов"""
    from sqlalchemy.orm import joinedload
    from app.models.order import Order
    from app.models.user import UserRole
    
    query = db.query(Order).options(
        joinedload(Order.buyer),
        joinedload(Order.supplier)
    )
    
    # Фильтрация в зависимости от роли
    if current_user.role == UserRole.ADMIN:
        # Админ видит все заказы
        pass
    elif current_user.role == UserRole.BUYER:
        # Заказчик видит только свои заказы
        query = query.filter(Order.buyer_id == current_user.id)
    elif current_user.role == UserRole.SUPPLIER:
        # Поставщик видит:
        # 1. Заказы без поставщика (на которые можно откликнуться)
        # 2. Заказы, на которые он уже откликнулся (supplier_id = его supplier_id)
        supplier = db.query(Supplier).filter(Supplier.user_id == current_user.id).first()
        
        # Если нет supplier, создаем его автоматически
        if not supplier:
            supplier = Supplier(
                name=current_user.organization_name or current_user.username,
                user_id=current_user.id,
                contact_info=current_user.email or ""
            )
            db.add(supplier)
            db.commit()
            db.refresh(supplier)
        
        # Показываем заказы без поставщика ИЛИ заказы, на которые он откликнулся
        query = query.filter(
            (Order.supplier_id.is_(None)) | (Order.supplier_id == supplier.id)
        )
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    
    return [format_order_response(order, db) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить заказ по ID"""
    from sqlalchemy.orm import joinedload
    from app.models.order import Order
    from app.models.user import UserRole
    from app.models.supplier import Supplier
    
    order = db.query(Order).options(
        joinedload(Order.buyer),
        joinedload(Order.supplier)
    ).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверка прав доступа
    if current_user.role == UserRole.ADMIN:
        pass  # Админ видит все
    elif current_user.role == UserRole.BUYER:
        # Заказчик видит только свои заказы
        if order.buyer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к этому заказу"
            )
    elif current_user.role == UserRole.SUPPLIER:
        # Поставщик видит заказы без поставщика ИЛИ заказы, на которые он откликнулся
        supplier = db.query(Supplier).filter(Supplier.user_id == current_user.id).first()
        
        # Если нет supplier, создаем его автоматически
        if not supplier:
            supplier = Supplier(
                name=current_user.organization_name or current_user.username,
                user_id=current_user.id,
                contact_info=current_user.email or ""
            )
            db.add(supplier)
            db.commit()
            db.refresh(supplier)
        
        # Видит заказы без поставщика ИЛИ свои заказы
        if order.supplier_id is not None and order.supplier_id != supplier.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к этому заказу"
            )
    
    return format_order_response(order, db)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Создать новый заказ"""
    from sqlalchemy.orm import joinedload
    from app.models.order import Order
    from app.models.user import User, UserRole
    from app.services import email_service
    
    try:
        db_order = order_service.create_order(db, order, current_user.id)
        
        # Отправляем email уведомления в фоне
        if not order.supplier_id:
            # Отправляем всем поставщикам с включенными уведомлениями
            suppliers = db.query(User).filter(
                User.role == UserRole.SUPPLIER,
                User.email_notifications == True,
                User.email.isnot(None)
            ).all()
            
            buyer_name = current_user.organization_name or current_user.username
            
            for supplier in suppliers:
                if supplier.email:
                    background_tasks.add_task(
                        email_service.send_order_notification_sync,
                        supplier_email=supplier.email,
                        order_title=db_order.title,
                        product_name=db_order.product_name,
                        delivery_volume=db_order.delivery_volume,
                        purchase_budget=db_order.purchase_budget,
                        deadline_at=db_order.deadline_at.isoformat(),
                        product_description=db_order.product_description,
                        buyer_name=buyer_name
                    )
        else:
            # Отправляем конкретному поставщику
            from app.models.supplier import Supplier
            supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
            if supplier and supplier.user_id:
                supplier_user = db.query(User).filter(User.id == supplier.user_id).first()
                if supplier_user and supplier_user.email_notifications and supplier_user.email:
                    buyer_name = current_user.organization_name or current_user.username
                    background_tasks.add_task(
                        email_service.send_order_notification_sync,
                        supplier_email=supplier_user.email,
                        order_title=db_order.title,
                        product_name=db_order.product_name,
                        delivery_volume=db_order.delivery_volume,
                        purchase_budget=db_order.purchase_budget,
                        deadline_at=db_order.deadline_at.isoformat(),
                        product_description=db_order.product_description,
                        buyer_name=buyer_name
                    )
        
        # Перезагружаем с отношениями
        db_order = db.query(Order).options(
            joinedload(Order.buyer),
            joinedload(Order.supplier)
        ).filter(Order.id == db_order.id).first()
        return format_order_response(db_order, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Обновить заказ"""
    from sqlalchemy.orm import joinedload
    
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверка прав доступа
    if current_user.role.value != "admin" and order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для изменения этого заказа"
        )
    
    from app.models.order import Order
    
    try:
        updated_order = order_service.update_order(db, order_id, order_update)
        # Перезагружаем с отношениями
        updated_order = db.query(Order).options(
            joinedload(Order.buyer),
            joinedload(Order.supplier)
        ).filter(Order.id == updated_order.id).first()
        return format_order_response(updated_order, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Удалить заказ"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверка прав доступа
    if current_user.role.value != "admin" and order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого заказа"
        )
    
    success = order_service.delete_order(db, order_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Изменить статус заказа"""
    from sqlalchemy.orm import joinedload
    from app.models.user import UserRole
    
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверка прав доступа
    if current_user.role == UserRole.ADMIN:
        pass  # Админ может менять статус любого заказа
    elif current_user.role == UserRole.BUYER:
        # Заказчик может менять статус только своих заказов
        if order.buyer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для изменения статуса этого заказа"
            )
    elif current_user.role == UserRole.SUPPLIER:
        # Поставщик не может менять статус заказа
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Поставщики не могут изменять статус заказа"
        )
    
    from app.models.order import Order
    
    updated_order = order_service.update_order_status(db, order_id, new_status)
    # Перезагружаем с отношениями
    updated_order = db.query(Order).options(
        joinedload(Order.buyer),
        joinedload(Order.supplier)
    ).filter(Order.id == updated_order.id).first()
    return format_order_response(updated_order, db)


@router.post("/{order_id}/respond", response_model=OrderResponse)
def respond_to_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Откликнуться на заказ (только для поставщиков)"""
    from sqlalchemy.orm import joinedload
    from app.models.user import UserRole
    from app.models.order import Order
    
    if current_user.role != UserRole.SUPPLIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только поставщики могут откликаться на заказы"
        )
    
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверяем, что заказ еще не взят
    if order.supplier_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот заказ уже взят другим поставщиком"
        )
    
    # Получаем supplier для текущего пользователя
    supplier = db.query(Supplier).filter(Supplier.user_id == current_user.id).first()
    if not supplier:
        # Автоматически создаем supplier, если его нет (для существующих пользователей)
        supplier = Supplier(
            name=current_user.organization_name or current_user.username,
            user_id=current_user.id,
            contact_info=current_user.email or ""
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
    
    # Обновляем заказ, привязывая его к поставщику
    order.supplier_id = supplier.id
    db.commit()
    db.refresh(order)
    
    # Перезагружаем с отношениями
    order = db.query(Order).options(
        joinedload(Order.buyer),
        joinedload(Order.supplier)
    ).filter(Order.id == order.id).first()
    
    return format_order_response(order, db)

