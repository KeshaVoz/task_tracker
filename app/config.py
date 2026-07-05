from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DATABASE_URL: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DB: int
    REDIS_URL: str  
    
    JWT_SECRET: str
    JWT_ALG: str
    ACCESS_TOKEN_TTL_MIN: int
    REFRESH_TOKEN_TTL_DAYS: int
    
    SMTP_HOST: str 
    SMTP_PORT: int 
    SMTP_USERNAME: Optional[str] = ""
    SMTP_PASSWORD: Optional[str] = ""  
    SMTP_FROM: str
    
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    CELERY_BROKER_URL: str

    KAFKA_URL: str

    ALLOWED_ORIGINS: List[str]
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_ignore_missing=True,
        extra="ignore"
    )

settings = Settings()


