from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Настройка пула соединений для продакшена
# pool_size - количество постоянных соединений
# max_overflow - максимальное количество дополнительных соединений
# pool_pre_ping - проверка соединения перед использованием (важно для продакшена)
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,  # 10 постоянных соединений
    max_overflow=20,  # до 20 дополнительных при нагрузке (итого до 30)
    pool_pre_ping=True,  # проверка соединения перед использованием
    pool_recycle=3600,  # пересоздавать соединения каждые 3600 секунд (1 час)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

