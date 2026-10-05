from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    admin_ids: str = ""
    admin_chat_id: int = 0
    support_chat_id: int = 0
    payment_details: str = "Реквизиты не заданы. Укажите PAYMENT_DETAILS в .env"
    webapp_url: str = ""
    webapp_host: str = "0.0.0.0"
    webapp_port: int = 8080
    database_path: str = "data/shop.db"

    @property
    def admin_id_set(self) -> set[int]:
        ids: set[int] = set()
        for chunk in self.admin_ids.split(","):
            chunk = chunk.strip()
            if chunk.isdigit() or (chunk.startswith("-") and chunk[1:].isdigit()):
                ids.add(int(chunk))
        return ids

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_id_set


settings = Settings()
