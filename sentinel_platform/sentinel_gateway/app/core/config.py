# sentinel_gateway/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentinel Gateway"
    ENV: str = "dev"
    
    # Message Bus
    NATS_URL: str = "nats://localhost:4222"
    
    # Security (For Phase 1, we accept this dummy secret)
    JWT_SECRET: str = "phase1-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()