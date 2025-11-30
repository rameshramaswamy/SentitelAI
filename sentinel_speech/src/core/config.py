# sentinel_speech/src/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model Config
    # Options: tiny, base, small, medium, large-v3
    # Use 'tiny' or 'base' for CPU development, 'small'/'medium' for GPU prod
    WHISPER_MODEL_SIZE: str = "base" 
    DEVICE: str = "cpu"  # Change to "cuda" if GPU is available
    COMPUTE_TYPE: str = "int8" # "float16" for GPU

    # VAD Settings
    VAD_THRESHOLD: float = 0.5  # Confidence level to trigger STT
    
    # Buffer Settings
    MIN_AUDIO_DURATION: float = 1.0  # Seconds of audio before transcribing
    MAX_AUDIO_DURATION: float = 30.0 # Force transcribe limit

    class Config:
        env_file = ".env"

settings = Settings()