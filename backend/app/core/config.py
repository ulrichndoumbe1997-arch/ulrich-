from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ULRICH Network Monitor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Base de données
    DATABASE_URL: str = "postgresql+asyncpg://ulrich:ulrich_secret@db:5432/ulrich"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"

    # Sécurité JWT
    SECRET_KEY: str = "change_me_in_production_please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 heures

    # Scanner réseau
    SCAN_INTERVAL_SECONDS: int = 60          # polling toutes les 60s
    PING_TIMEOUT: float = 0.5               # timeout ping en secondes
    PING_COUNT: int = 1                     # nombre de pings par équipement
    NMAP_SCAN_ARGS: str = "-sV -O --osscan-guess -T4"
    SNMP_COMMUNITY: str = "public"
    SNMP_PORT: int = 161
    SNMP_TIMEOUT: int = 2

    # Alertes email (optionnel, configurable depuis l'interface)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "ulrich-monitor@gmail.com"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
