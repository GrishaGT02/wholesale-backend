import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.core.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
) -> bool:
    """
    Отправка email через SMTP
    
    Args:
        to_email: Email получателя
        subject: Тема письма
        html_body: HTML тело письма
        text_body: Текстовое тело письма (опционально)
    
    Returns:
        True если отправка успешна, False в противном случае
    """
    # Если SMTP не настроен, просто логируем
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(f"SMTP не настроен. Письмо было бы отправлено на {to_email}: {subject}")
        return False
    
    try:
        # Создаем сообщение
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        
        # Добавляем текстовую версию (если есть)
        if text_body:
            text_part = MIMEText(text_body, "plain", "utf-8")
            message.attach(text_part)
        
        # Добавляем HTML версию
        html_part = MIMEText(html_body, "html", "utf-8")
        message.attach(html_part)
        
        # Отправляем через SMTP
        # Для Gmail: порт 587 использует STARTTLS, порт 465 использует SSL
        if settings.SMTP_PORT == 465:
            # SSL соединение (порт 465)
            import ssl
            context = ssl.create_default_context()
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                tls_context=context,
                use_tls=True
            )
        else:
            # STARTTLS соединение (порт 587)
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )
        
        logger.info(f"Email успешно отправлен на {to_email}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке email на {to_email}: {str(e)}")
        return False


async def send_order_notification(
    supplier_email: str,
    order_title: str,
    product_name: str,
    delivery_volume: Optional[str],
    purchase_budget: Optional[float],
    deadline_at: str,
    product_description: Optional[str],
    buyer_name: str
) -> bool:
    """
    Отправка уведомления поставщику о новом заказе
    
    Args:
        supplier_email: Email поставщика
        order_title: Название заказа
        product_name: Наименование товара
        delivery_volume: Объем поставки
        purchase_budget: Бюджет закупки
        deadline_at: Сроки доставки
        product_description: Описание товара
        buyer_name: Имя покупателя
    
    Returns:
        True если отправка успешна, False в противном случае
    """
    # Форматируем дату
    from datetime import datetime
    try:
        deadline = datetime.fromisoformat(deadline_at.replace('Z', '+00:00'))
        deadline_str = deadline.strftime("%d.%m.%Y %H:%M")
    except:
        deadline_str = deadline_at
    
    # Форматируем бюджет
    budget_str = ""
    if purchase_budget:
        budget_str = f"{purchase_budget:,.2f} ₽".replace(',', ' ')
    
    # HTML шаблон письма
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
            .info-row {{ margin-bottom: 15px; }}
            .label {{ font-weight: bold; color: #555; }}
            .value {{ color: #333; margin-top: 5px; }}
            .button {{ display: inline-block; background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #777; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Новый заказ на поставку товаров</h1>
            </div>
            <div class="content">
                <p>Здравствуйте!</p>
                <p>Поступил новый заказ на поставку товаров из Китая.</p>
                
                <div class="info-row">
                    <div class="label">Название заказа:</div>
                    <div class="value">{order_title}</div>
                </div>
                
                <div class="info-row">
                    <div class="label">Наименование товара:</div>
                    <div class="value">{product_name}</div>
                </div>
                
                {f'<div class="info-row"><div class="label">Объем поставки:</div><div class="value">{delivery_volume}</div></div>' if delivery_volume else ''}
                
                {f'<div class="info-row"><div class="label">Бюджет закупки:</div><div class="value">{budget_str}</div></div>' if budget_str else ''}
                
                <div class="info-row">
                    <div class="label">Сроки доставки:</div>
                    <div class="value">{deadline_str}</div>
                </div>
                
                {f'<div class="info-row"><div class="label">Описание товара:</div><div class="value">{product_description}</div></div>' if product_description else ''}
                
                <div class="info-row">
                    <div class="label">Заказчик:</div>
                    <div class="value">{buyer_name}</div>
                </div>
                
                <p style="margin-top: 20px;">
                    <a href="http://localhost:5173" class="button">Перейти к заказу</a>
                </p>
            </div>
            <div class="footer">
                <p>Это автоматическое уведомление от системы Wholesale Aggregator</p>
                <p>Если вы не хотите получать такие уведомления, вы можете отключить их в настройках личного кабинета.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Текстовая версия
    text_body = f"""
Новый заказ на поставку товаров

Здравствуйте!

Поступил новый заказ на поставку товаров из Китая.

Название заказа: {order_title}
Наименование товара: {product_name}
{f'Объем поставки: {delivery_volume}' if delivery_volume else ''}
{f'Бюджет закупки: {budget_str}' if budget_str else ''}
Сроки доставки: {deadline_str}
{f'Описание товара: {product_description}' if product_description else ''}
Заказчик: {buyer_name}

Перейдите в личный кабинет для просмотра деталей заказа.

Это автоматическое уведомление от системы Wholesale Aggregator.
Если вы не хотите получать такие уведомления, вы можете отключить их в настройках личного кабинета.
    """
    
    subject = f"Новый заказ: {order_title}"
    
    return await send_email(supplier_email, subject, html_body, text_body)


def send_order_notification_sync(
    supplier_email: str,
    order_title: str,
    product_name: str,
    delivery_volume: Optional[str],
    purchase_budget: Optional[float],
    deadline_at: str,
    product_description: Optional[str],
    buyer_name: str
) -> None:
    """
    Синхронная обёртка для отправки уведомления поставщику
    Используется с BackgroundTasks
    """
    try:
        # Для BackgroundTasks создаем новый event loop
        # так как они работают в отдельном потоке
        asyncio.run(
            send_order_notification(
                supplier_email, order_title, product_name, delivery_volume,
                purchase_budget, deadline_at, product_description, buyer_name
            )
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке email уведомления: {str(e)}")