from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.message import Message
from app.models.order import Order
from app.models.user import User
from app.schemas.message import MessageCreate


def get_messages_by_order(
    db: Session,
    order_id: int,
    current_user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Message]:
    """Получить сообщения по заказу (только для участников заказа)"""
    from app.models.user import UserRole
    from app.models.supplier import Supplier
    
    # Проверяем, что пользователь является участником заказа
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return []
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        return []
    
    # Проверяем права доступа
    is_buyer = order.buyer_id == current_user_id
    is_supplier = False
    
    # Если пользователь - поставщик, разрешаем просмотр даже если заказ еще не взят
    if user.role == UserRole.SUPPLIER:
        supplier = db.query(Supplier).filter(Supplier.user_id == current_user_id).first()
        if supplier:
            # Заказ взят этим поставщиком или еще свободен
            if order.supplier_id == supplier.id or order.supplier_id is None:
                is_supplier = True
        else:
            # Нет Supplier записи, но роль поставщик - разрешаем
            is_supplier = True
    elif order.supplier_id:
        # Для не-поставщиков проверяем только если заказ уже взят
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        if supplier and supplier.user_id == current_user_id:
            is_supplier = True
    
    if not (is_buyer or is_supplier):
        return []
    
    # Получаем сообщения
    return db.query(Message).filter(
        Message.order_id == order_id
    ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()


def create_message(
    db: Session,
    message: MessageCreate,
    sender_id: int
) -> Message:
    """Создать новое сообщение"""
    from app.models.user import UserRole
    from app.models.supplier import Supplier
    
    # Проверяем, что заказ существует и пользователь имеет доступ
    order = db.query(Order).filter(Order.id == message.order_id).first()
    if not order:
        raise ValueError("Заказ не найден")
    
    sender = db.query(User).filter(User.id == sender_id).first()
    if not sender:
        raise ValueError("Отправитель не найден")
    
    # Проверяем, что sender является участником заказа
    is_sender_buyer = order.buyer_id == sender_id
    is_sender_supplier = False
    
    # Если отправитель - поставщик по роли, разрешаем отправку даже если заказ еще не взят
    if sender.role == UserRole.SUPPLIER:
        # Проверяем, есть ли у поставщика Supplier запись
        supplier = db.query(Supplier).filter(Supplier.user_id == sender_id).first()
        if supplier:
            # Если заказ уже взят этим поставщиком
            if order.supplier_id == supplier.id:
                is_sender_supplier = True
            # Или если заказ еще свободен - тоже разрешаем (будет отклик при первой отправке)
            elif order.supplier_id is None:
                is_sender_supplier = True
        # Если нет Supplier записи, но роль поставщик - разрешаем (будет создана при отклике)
        else:
            is_sender_supplier = True
    elif order.supplier_id:
        # Для не-поставщиков проверяем только если заказ уже взят
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        if supplier and supplier.user_id == sender_id:
            is_sender_supplier = True
    
    if not (is_sender_buyer or is_sender_supplier):
        raise ValueError("Нет доступа к этому заказу")
    
    # Проверяем, что receiver тоже участник
    receiver = db.query(User).filter(User.id == message.receiver_id).first()
    if not receiver:
        raise ValueError("Получатель не найден")
    
    # Определяем, является ли receiver участником заказа
    is_receiver_buyer = order.buyer_id == message.receiver_id
    is_receiver_supplier = False
    
    # Если получатель - поставщик по роли и заказ еще свободен, разрешаем
    if receiver.role == UserRole.SUPPLIER:
        supplier = db.query(Supplier).filter(Supplier.user_id == message.receiver_id).first()
        if supplier:
            if order.supplier_id == supplier.id or order.supplier_id is None:
                is_receiver_supplier = True
        else:
            is_receiver_supplier = True
    elif order.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        if supplier and supplier.user_id == message.receiver_id:
            is_receiver_supplier = True
    
    if not (is_receiver_buyer or is_receiver_supplier):
        raise ValueError("Получатель не является участником этого заказа")
    
    # Проверяем, что sender и receiver разные пользователи
    if sender_id == message.receiver_id:
        raise ValueError("Нельзя отправить сообщение самому себе")
    
    db_message = Message(
        order_id=message.order_id,
        sender_id=sender_id,
        receiver_id=message.receiver_id,
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def mark_message_as_read(
    db: Session,
    message_id: int,
    user_id: int
) -> Optional[Message]:
    """Отметить сообщение как прочитанное"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        return None
    
    # Проверяем, что пользователь является получателем
    if message.receiver_id != user_id:
        return None
    
    if not message.read_at:
        from datetime import datetime
        message.read_at = datetime.utcnow()
        db.commit()
        db.refresh(message)
    
    return message


def get_user_chats(db: Session, user_id: int) -> List[dict]:
    """Получить все чаты пользователя (заказы с сообщениями)"""
    from sqlalchemy import func, or_, and_
    from app.models.supplier import Supplier
    
    # Получаем все заказы, где пользователь является участником (buyer или supplier)
    # и есть хотя бы одно сообщение
    orders_with_messages = db.query(Order).join(Message, Order.id == Message.order_id).distinct().all()
    
    chats = []
    for order in orders_with_messages:
        # Проверяем, является ли пользователь участником
        is_buyer = order.buyer_id == user_id
        is_supplier = False
        other_user_id = None
        other_user_name = None
        
        if order.supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
            if supplier and supplier.user_id == user_id:
                is_supplier = True
                other_user_id = order.buyer_id
                other_user_name = order.buyer.username if order.buyer else "Неизвестно"
        
        if is_buyer:
            if order.supplier_id:
                supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
                if supplier and supplier.user_id:
                    other_user_id = supplier.user_id
                    other_user = db.query(User).filter(User.id == supplier.user_id).first()
                    other_user_name = other_user.username if other_user else "Неизвестно"
            else:
                continue  # Пропускаем заказы без поставщика
        
        if not (is_buyer or is_supplier) or not other_user_id:
            continue
        
        # Получаем последнее сообщение
        last_message = db.query(Message).filter(
            Message.order_id == order.id
        ).order_by(Message.created_at.desc()).first()
        
        # Считаем непрочитанные сообщения (где пользователь получатель и read_at = None)
        unread_count = db.query(func.count(Message.id)).filter(
            and_(
                Message.order_id == order.id,
                Message.receiver_id == user_id,
                Message.read_at.is_(None)
            )
        ).scalar() or 0
        
        chats.append({
            "order_id": order.id,
            "order_title": order.title,
            "other_user_id": other_user_id,
            "other_user_name": other_user_name,
            "last_message": last_message.content if last_message else None,
            "last_message_time": last_message.created_at if last_message else None,
            "unread_count": unread_count
        })
    
    # Сортируем по времени последнего сообщения (новые сверху)
    chats.sort(key=lambda x: x["last_message_time"] or datetime.min, reverse=True)
    
    return chats


def mark_all_messages_as_read_in_order(
    db: Session,
    order_id: int,
    user_id: int
) -> int:
    """Пометить все непрочитанные сообщения в заказе как прочитанные для пользователя"""
    from datetime import datetime
    
    # Проверяем, что пользователь является участником заказа
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return 0
    
    # Проверяем права доступа
    is_buyer = order.buyer_id == user_id
    is_supplier = False
    if order.supplier_id:
        from app.models.supplier import Supplier
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        if supplier and supplier.user_id == user_id:
            is_supplier = True
    
    if not (is_buyer or is_supplier):
        return 0
    
    # Помечаем все непрочитанные сообщения, где пользователь получатель
    updated = db.query(Message).filter(
        Message.order_id == order_id,
        Message.receiver_id == user_id,
        Message.read_at.is_(None)
    ).update(
        {"read_at": datetime.utcnow()},
        synchronize_session=False
    )
    
    db.commit()
    return updated


