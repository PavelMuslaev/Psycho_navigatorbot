from os import getenv
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    api_base_url: str


@lru_cache
def get_settings() -> Settings:
    load_dotenv()

    bot_token = getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set!")

    api_base_url = getenv("API_BASE_URL")
    if not api_base_url:
        raise RuntimeError("API_BASE_URL is not set!")

    return Settings(bot_token, api_base_url)
