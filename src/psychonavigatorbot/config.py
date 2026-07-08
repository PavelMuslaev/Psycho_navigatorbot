from os import getenv

from dotenv import load_dotenv


def get_bot_token() -> str:
    load_dotenv()

    token = getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set!")

    return token
