import asyncio
from aiogram import Dispatcher, Bot, Router
from aiohttp import ClientSession, ClientTimeout

from psychonavigatorbot.routers import setup_router
from psychonavigatorbot.config import get_settings
from psychonavigatorbot.services.tests_api import QuestionnaireApiClient


def create_dispatcher(r: Router) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(r)

    return dispatcher


async def main():
    settings = get_settings()

    bot = Bot(token=settings.bot_token)
    dispatcher = create_dispatcher(setup_router())

    timeout = ClientTimeout(total=5)
    async with ClientSession(timeout=timeout) as session:
        api_client = QuestionnaireApiClient(settings, session)

        await dispatcher.start_polling(bot, api_client=api_client)


if __name__ == "__main__":
    asyncio.run(main())
