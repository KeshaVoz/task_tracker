from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    REDIS_PASSWORD: str
    REDIS_URL: str
    REDIS_HOST: str
    REDIS_PORT: int

    JWT_SECRET: str
    JWT_ALG: str
    ACCESS_TOKEN_TTL_MIN: int
    REFRESH_TOKEN_TTL_DAYS: int

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()

DATABASE_URL = f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'