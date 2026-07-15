from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "AeroClub - Automação de Balizamento"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite+aiosqlite:///./aeroclub.db"
    DATABASE_URL_SYNC: str = "sqlite:///./aeroclub.db"

    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REDIS_URL: str = "redis://localhost:6379/0"

    WHATSAPP_API_URL: str = "https://graph.facebook.com/v17.0"
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_TOKEN: Optional[str] = None

    CAMERA_IP: Optional[str] = None
    CAMERA_USER: Optional[str] = None
    CAMERA_PASSWORD: Optional[str] = None

    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_USER: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]

    class Config:
        env_file = ".env"


settings = Settings()
