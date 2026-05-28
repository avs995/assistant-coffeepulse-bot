import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bot_token: str
    owner_id: int
    database_path: str


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN")
    owner_id_raw = os.getenv("OWNER_ID")
    database_path = os.getenv("DATABASE_PATH", "data/sales_assistant.sqlite3")

    if not bot_token:
        raise ValueError("BOT_TOKEN is required")

    if not owner_id_raw:
        raise ValueError("OWNER_ID is required")

    try:
        owner_id = int(owner_id_raw)
    except ValueError as exc:
        raise ValueError("OWNER_ID must be an integer") from exc

    return Settings(
        bot_token=bot_token,
        owner_id=owner_id,
        database_path=database_path,
    )


settings = load_settings()
