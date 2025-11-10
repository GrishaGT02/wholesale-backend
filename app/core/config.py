from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os
import json


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
    # Делаем Union чтобы принимать и строку и список
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    
    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        # Если это уже список, возвращаем как есть
        if isinstance(v, list):
            return v
        # Если это строка
        if isinstance(v, str):
            # Если пустая строка, возвращаем значения по умолчанию
            if not v.strip():
                return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
            # Пытаемся распарсить как JSON (если это JSON массив)
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            # Если не JSON, разбиваем по запятой
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # Если ничего не подошло, возвращаем значения по умолчанию
        return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    
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


# Создаем settings - валидатор автоматически обработает BACKEND_CORS_ORIGINS
settings = Settings()

