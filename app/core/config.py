from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Optional
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
    
    # CORS - делаем опциональным и обрабатываем через валидатор
    BACKEND_CORS_ORIGINS: Optional[List[str]] = Field(
        default=None,
        exclude=True  # Исключаем из сериализации и чтения env
    )
    
    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        # Если значение уже список, возвращаем как есть
        if isinstance(v, list):
            return v
        # Если None или пустая строка, возвращаем None (обработаем после создания)
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        # Если строка, пытаемся разбить по запятой
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_ignore_empty=True,
        # Исключаем BACKEND_CORS_ORIGINS из чтения env
        extra='ignore',
    )
    
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


# Сначала читаем BACKEND_CORS_ORIGINS из env вручную (до создания Settings)
cors_env = os.getenv("BACKEND_CORS_ORIGINS")
if cors_env and cors_env.strip():
    # Если переменная задана и не пустая, разбиваем по запятой
    cors_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
else:
    # Если переменная не задана или пустая, используем значения по умолчанию
    cors_origins = [
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://chinapspace.online",
        "https://www.chinapspace.online"
    ]

# Временно удаляем переменную из env, чтобы pydantic-settings не пытался её читать
if "BACKEND_CORS_ORIGINS" in os.environ:
    del os.environ["BACKEND_CORS_ORIGINS"]

# Создаем settings (BACKEND_CORS_ORIGINS не будет читаться из env)
settings = Settings()

# Устанавливаем значение CORS вручную
settings.BACKEND_CORS_ORIGINS = cors_origins

