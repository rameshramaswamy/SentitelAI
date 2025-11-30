# Database, S3, and Qdrant Settings# sentinel_data/src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    DATABASE_URL: str = "postgresql+asyncpg://sentinel:sentinel_pass@localhost:5432/sentinel_db"
    
    # S3 Settings (MinIO for Dev)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "sentinel-audio"

    # Vector DB
    QDRANT_URL: str = "http://localhost:6333"

    class Config:
        env_file = ".env"

settings = Settings()