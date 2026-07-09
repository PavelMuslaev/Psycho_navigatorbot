import asyncio
from aiogram import Dispatcher, Bot, Router

from psychonavigatorbot.handlers import setup_router
from psychonavigatorbot.config import get_settings


def create_dispatcher(r: Router) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(r)

    return dispatcher


async def main():
    settings = get_settings()

    bot = Bot(token=settings.bot_token)
    dispatcher = create_dispatcher(setup_router())
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
