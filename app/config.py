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
    
    MAILJET_HOST: str 
    MAILJET_PORT: int 
    MAILJET_USERNAME: str  
    MAILJET_PASSWORD: str  
    MAILJET_FROM: str
    
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    
    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()


