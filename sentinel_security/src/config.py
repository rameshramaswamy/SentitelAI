# sentinel_security/src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Toggle specific scrubbers
    SCRUB_CREDIT_CARDS: bool = True
    SCRUB_SSN: bool = True
    SCRUB_EMAIL: bool = True
    SCRUB_PHONE: bool = True
    
    # Replacement string format
    REDACTION_MASK: str = "[REDACTED_{type}]"
    MASTER_KEY: str = os.getenv("MASTER_KEY", "ChangeMeToAValid32ByteBase64KeyForProduction==")
    class Config:
        env_file = ".env"

settings = Settings()