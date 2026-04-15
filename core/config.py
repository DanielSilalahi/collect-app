from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:@localhost/collection_db"
    JWT_SECRET: str = "c0ll3ct10n_s3cr3t_k3y_ch4ng3_th1s_1n_pr0duct10n"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440  # 24 hours
    SESSION_SECRET: str = "s3ss10n_s3cr3t_k3y_ch4ng3_th1s"
    UPLOAD_DIR: str = str(BASE_DIR / "static" / "uploads")

    class Config:
        env_file = str(BASE_DIR / ".env")

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(str(BASE_DIR / "static" / "uploads" / "temp"), exist_ok=True)
