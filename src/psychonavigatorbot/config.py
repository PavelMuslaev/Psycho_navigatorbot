from os import getenv
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    api_base_url: str
    telegram_proxy_url: str | None
    telegram_request_timeout: float


@lru_cache
def get_settings() -> Settings:
    load_dotenv()

    bot_token = getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set!")

    api_base_url = getenv("API_BASE_URL")
    if not api_base_url:
        raise RuntimeError("API_BASE_URL is not set!")

    telegram_request_timeout = float(getenv("TELEGRAM_REQUEST_TIMEOUT", "60"))
    telegram_proxy_url = getenv("TELEGRAM_PROXY_URL") or None

    return Settings(
        bot_token=bot_token,
        api_base_url=api_base_url,
        telegram_proxy_url=telegram_proxy_url,
        telegram_request_timeout=telegram_request_timeout,
    )
