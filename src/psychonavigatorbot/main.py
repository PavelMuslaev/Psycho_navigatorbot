import asyncio
from aiogram import Dispatcher, Bot, Router

from handlers.start import router
from config import get_bot_token


def create_dispatcher(r: Router) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(r)

    return dispatcher


async def main():
    bot = Bot(token=get_bot_token())
    dispatcher = create_dispatcher(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
