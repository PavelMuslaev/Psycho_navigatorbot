import aiohttp
from pydantic import TypeAdapter
from psychonavigatorbot.config import Settings
from psychonavigatorbot.models.test import Questionnaire, TestSummary

TEST_ADAPTER = TypeAdapter(tuple[TestSummary])


class QuestionnaireApiClient:
    def __init__(self, settings: Settings, session: aiohttp.ClientSession):
        self.url = f"{settings.api_base_url}/tests"
        self.session = session

    async def get_tests(self) -> tuple[TestSummary, ...]:
        async with self.session.get(self.url) as response:
            if response.status != 200:
                raise ValueError(f"Request failed with status code {response.status}")
            return TEST_ADAPTER.validate_python(await response.json())

    async def get_questionnaire(self, questionnaire_id: int) -> Questionnaire:
        async with self.session.get(f"{self.url}/{questionnaire_id}") as response:
            if response.status != 200:
                raise ValueError(f"Request failed with status code {response.status}")
            return Questionnaire.model_validate(await response.json())
