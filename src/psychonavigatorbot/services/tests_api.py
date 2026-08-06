import aiohttp
from pydantic import TypeAdapter

from psychonavigatorbot.exceptions.tests import ApiClientError
from psychonavigatorbot.models.test import Questionnaire, TestSummary

TEST_ADAPTER = TypeAdapter(list[TestSummary])


class QuestionnaireApiClient:
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self._url = f"{base_url}/tests"
        self._session = session

    async def get_tests(self) -> list[TestSummary]:
        async with self._session.get(self._url) as response:
            if response.status != 200:
                raise ApiClientError(
                    f"Request failed with status code {response.status}"
                )
            return TEST_ADAPTER.validate_python(await response.json())

    async def get_questionnaire(self, questionnaire_id: int) -> Questionnaire:
        async with self._session.get(f"{self._url}/{questionnaire_id}") as response:
            if response.status != 200:
                raise ApiClientError(
                    f"Request failed with status code {response.status}"
                )
            return Questionnaire.model_validate(await response.json())
