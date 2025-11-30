# sentinel_integrations/src/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # LLM Settings
    OPENAI_API_KEY: str = "sk-placeholder"
    LLM_MODEL: str = "gpt-4o-mini" # Cost-effective & fast
    LLM_MOCK_MODE: bool = True # Set to False to actually spend money
    
    # Path to templates
    TEMPLATE_DIR: str = "templates"

   # CRM Settings
    CRM_PROVIDER: str = "salesforce" # or "mock", "hubspot"
    
    # Salesforce Credentials (Production/Sandbox)
    SF_USERNAME: str = "demo@example.com"
    SF_PASSWORD: str = "password"
    SF_TOKEN: str = "security_token"
    SF_DOMAIN: str = "login" # or 'test' for sandbox
    
    class Config:
        env_file = ".env"

settings = Settings()