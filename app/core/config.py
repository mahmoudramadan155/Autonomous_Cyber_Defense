from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Cyber Defense Platform"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://soc:soc_secure_pass@postgres:5432/soc_db"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "change-me-in-production"
    response_mode: str = "auto"  # auto | manual
    model_path: str = "data/model.joblib"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
