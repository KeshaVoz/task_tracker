from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    KAFKA_URL: str

    LLM_CREDENTIALS: str
    LLM_MODEL: str

    SUMMARY_DB_HOST: str
    SUMMARY_DB_PORT: int
    SUMMARY_DB_NAME: str
    SUMMARY_DB_USER: str
    SUMMARY_DB_PASSWORD: str
    SUMMARY_DATABASE_URL: str
    
    model_config = SettingsConfigDict(
        env_file='../.env', 
        env_file_ignore_missing=True,
        extra='ignore'
    )


settings = Settings()