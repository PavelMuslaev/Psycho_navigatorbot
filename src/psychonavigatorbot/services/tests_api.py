import aiohttp
from psychonavigatorbot.config import get_settings
from psychonavigatorbot.models.test import Test


async def get_tests() -> list[Test] | None:
    settings = get_settings()
    url = f"{settings.api_base_url}/tests/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None
