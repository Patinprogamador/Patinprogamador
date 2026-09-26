from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-5"

    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_api_version: str = "v20.0"

    restaurant_name: str = "Pizzaria Bella Napoli"
    restaurant_address: str = "Rua das Palmeiras, 123 - São Paulo, SP"
    restaurant_phone: str = "(11) 4444-5555"

    database_path: str = "data/orders.db"
    menu_path: str = "data/menu.json"
    faq_path: str = "data/faq.json"

    def resolved_database_path(self) -> Path:
        path = Path(self.database_path)
        return path if path.is_absolute() else BASE_DIR / path

    def resolved_menu_path(self) -> Path:
        path = Path(self.menu_path)
        return path if path.is_absolute() else BASE_DIR / path

    def resolved_faq_path(self) -> Path:
        path = Path(self.faq_path)
        return path if path.is_absolute() else BASE_DIR / path


def get_settings() -> Settings:
    return Settings()
