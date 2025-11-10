from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse, ChatInfo

router = APIRouter()


def format_message_response(message: Message) -> MessageResponse:
    """Форматирование ответа сообщения"""
    return MessageResponse(
        id=message.id,
        order_id=message.order_id,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        created_at=message.created_at,
        read_at=message.read_at,
        sender={
            "id": message.sender.id,
            "username": message.sender.username
        } if message.sender else None,
        receiver={
            "id": message.receiver.id,
            "username": message.receiver.username
        } if message.receiver else None
    )


@router.get("/orders/{order_id}/messages", response_model=List[MessageResponse])
def get_order_messages(
    order_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить сообщения по заказу"""
    from app.services import message_service
    
    # Проверяем доступ и получаем сообщения через сервис
    messages = message_service.get_messages_by_order(db, order_id, current_user.id, skip, limit)
    if not messages:
        # Если нет доступа, возвращаем пустой список
        return []
    
    # Перезагружаем с отношениями
    messages_with_relations = db.query(Message).options(
        joinedload(Message.sender),
        joinedload(Message.receiver)
    ).filter(Message.order_id == order_id).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
    
    return [format_message_response(msg) for msg in messages_with_relations]


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Отправить сообщение"""
    from app.services import message_service
    from sqlalchemy.orm import joinedload
    
    try:
        db_message = message_service.create_message(db, message, current_user.id)
        # Перезагружаем с отношениями
        db_message = db.query(Message).options(
            joinedload(Message.sender),
            joinedload(Message.receiver)
        ).filter(Message.id == db_message.id).first()
        return format_message_response(db_message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/messages/{message_id}/read", response_model=MessageResponse)
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Отметить сообщение как прочитанное"""
    from app.services import message_service
    from sqlalchemy.orm import joinedload
    
    message = message_service.mark_message_as_read(db, message_id, current_user.id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено или нет доступа"
        )
    
    # Перезагружаем с отношениями
    message = db.query(Message).options(
        joinedload(Message.sender),
        joinedload(Message.receiver)
    ).filter(Message.id == message.id).first()
    
    return format_message_response(message)


@router.get("/messages/chats", response_model=List[ChatInfo])
def get_user_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить все чаты пользователя (список заказов с сообщениями)"""
    from app.services import message_service
    
    chats = message_service.get_user_chats(db, current_user.id)
    return [ChatInfo(**chat) for chat in chats]


@router.post("/orders/{order_id}/messages/mark-all-read")
def mark_all_messages_read_in_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Пометить все непрочитанные сообщения в заказе как прочитанные"""
    from app.services import message_service
    
    count = message_service.mark_all_messages_as_read_in_order(db, order_id, current_user.id)
    return {"marked_count": count}

