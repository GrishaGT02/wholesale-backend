"""
Скрипт для инициализации базы данных с тестовыми данными
"""
import sys
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.supplier import Supplier
from app.models.order import Order, OrderStatus
from datetime import datetime, timedelta

# Создаем все таблицы
Base.metadata.create_all(bind=engine)

db: Session = SessionLocal()


def init_db():
    """Инициализация базы данных с тестовыми данными"""
    
    # Создаем админа
    admin = User(
        email="admin@example.com",
        username="admin",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print("✓ Создан администратор: admin / admin123")
    
    # Создаем тестового покупателя
    buyer = User(
        email="buyer@example.com",
        username="vnasonov2012",
        password_hash=get_password_hash("buyer123"),
        role=UserRole.BUYER
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    print("✓ Создан покупатель: vnasonov2012 / buyer123")
    
    # Создаем поставщиков
    supplier1 = Supplier(
        name="Китайский поставщик #1",
        contact_info="+86 123 456 7890",
        country="China",
        rating=4.5
    )
    db.add(supplier1)
    db.commit()
    db.refresh(supplier1)
    
    supplier2 = Supplier(
        name="Оптовый поставщик товаров",
        contact_info="supplier@china.com",
        country="China",
        rating=4.8
    )
    db.add(supplier2)
    db.commit()
    db.refresh(supplier2)
    print("✓ Созданы поставщики")
    
    # Создаем тестовый заказ (как на скриншоте)
    test_order = Order(
        title="Индивидуальный заказ gulhasangrigor #3",
        buyer_id=buyer.id,
        supplier_id=supplier1.id,
        ordered_at=datetime(2024, 11, 1, 17, 52),
        deadline_at=datetime.utcnow() + timedelta(days=29, hours=23),
        cost=24000.0,
        note="Тестовая заметка",
        status=OrderStatus.IN_PROGRESS
    )
    db.add(test_order)
    db.commit()
    db.refresh(test_order)
    print("✓ Создан тестовый заказ")
    
    print("\n✓ База данных успешно инициализирована!")
    print("\nТестовые учетные данные:")
    print("  Админ: admin / admin123")
    print("  Покупатель: vnasonov2012 / buyer123")


if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        print(f"Ошибка: {e}")
        db.rollback()
        raise
    finally:
        db.close()

