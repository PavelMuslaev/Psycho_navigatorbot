import asyncio
import logging

from aiogram import Dispatcher, Bot, Router
from aiogram.fsm.storage.memory import (
    MemoryStorage,       # Встроенный формат хранения состояний (При перезапуске сбрасывается)
    SimpleEventIsolation # SimpleEventIsolation последовательно обрабатывает события одного пользователя.
)
from aiohttp import ClientSession, ClientTimeout

from psychonavigatorbot.routers import setup_router
from psychonavigatorbot.config import get_settings
from psychonavigatorbot.services.tests_api import QuestionnaireApiClient


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_dispatcher(r: Router) -> Dispatcher:
    dispatcher = Dispatcher(
        storage=MemoryStorage(),
        events_isolation=SimpleEventIsolation(),
    )
    dispatcher.include_router(r)

    return dispatcher


async def main():
    settings = get_settings()

    bot = Bot(token=settings.bot_token)
    dispatcher = create_dispatcher(setup_router())

    timeout = ClientTimeout(total=5)
    async with ClientSession(timeout=timeout) as session:
        api_client = QuestionnaireApiClient(settings.api_base_url, session)

        await dispatcher.start_polling(bot, api_client=api_client)


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
