from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    order_id: int
    receiver_id: int


class MessageSender(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class MessageReceiver(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class MessageResponse(MessageBase):
    id: int
    order_id: int
    sender_id: int
    receiver_id: int
    sender: Optional[MessageSender] = None
    receiver: Optional[MessageReceiver] = None
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Message(MessageResponse):
    pass


class ChatInfo(BaseModel):
    """Информация о чате (заказ с перепиской)"""
    order_id: int
    order_title: str
    other_user_id: int
    other_user_name: str
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    
    class Config:
        from_attributes = True


