from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{(BASE_DIR / 'var' / 'shop.db').as_posix()}"
    dev_user_email: str = "demo@example.com"
    dev_user_name: str = "演示用户"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_prefix="SHOP_",
        extra="ignore",
    )


settings = Settings()

