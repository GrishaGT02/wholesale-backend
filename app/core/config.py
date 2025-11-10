from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Wholesale Aggregator API"
    DEBUG: bool = False  # ВАЖНО: установите False в продакшене!
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/wholesale_aggregator"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  
    
    # CORS - НЕ объявляем здесь, читаем полностью вручную через os.getenv()
    # Это поле будет добавлено после создания Settings
    
    # Email settings - SMTP сервер для отправки писем от имени приложения
    # Все письма будут отправляться через этот SMTP сервер
    # Пользователи получат письма на свои email адреса (указанные при регистрации)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""  # Email приложения для отправки (например, noreply@yourdomain.com)
    SMTP_PASSWORD: str = ""  # Пароль для SMTP сервера приложения
    SMTP_FROM_EMAIL: str = "noreply@wholesale-aggregator.com"  # От кого отправляются письма
    SMTP_FROM_NAME: str = "Wholesale Aggregator"  # Имя отправителя
    SMTP_USE_TLS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Создаем settings (BACKEND_CORS_ORIGINS не объявлен в классе, поэтому pydantic-settings не будет его читать)
settings = Settings()

# Читаем BACKEND_CORS_ORIGINS полностью вручную через os.getenv()
cors_env = os.getenv("BACKEND_CORS_ORIGINS")
if cors_env and cors_env.strip():
    # Если переменная задана и не пустая, разбиваем по запятой
    settings.BACKEND_CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
else:
    # Если переменная не задана или пустая, используем значения по умолчанию
    settings.BACKEND_CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

