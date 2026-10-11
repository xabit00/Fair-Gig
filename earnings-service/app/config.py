from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


SERVICE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(SERVICE_DIR / ".env")
load_dotenv(SERVICE_DIR.parent / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fairgig")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-this-development-secret-now")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )


settings = Settings()

