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
    
    # CORS - используем строку или список
    # В продакшене можно использовать переменную окружения или список
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    
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


settings = Settings()

# Поддержка CORS из переменной окружения (строка через запятую)
# Это нужно для Render.com и других платформ
cors_env = os.getenv("BACKEND_CORS_ORIGINS")
if cors_env:
    settings.BACKEND_CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

