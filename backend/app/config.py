from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{(BASE_DIR / 'var' / 'shop.db').as_posix()}"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_prefix="SHOP_",
        extra="ignore",
    )


settings = Settings()

