import aiohttp
from pydantic import TypeAdapter, ValidationError

from psychonavigatorbot.exceptions.tests import (
    ApiClientError,
    ApiUnavailableError,
    ApiNotFoundError,
)
from psychonavigatorbot.models.test import Questionnaire, TestSummary

TEST_ADAPTER = TypeAdapter(list[TestSummary])


class QuestionnaireApiClient:
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self._url = f"{base_url}/tests"
        self._session = session

    async def get_tests(self) -> list[TestSummary]:
        response = self._get_json(self._url)
        try:
            return TEST_ADAPTER.validate_python(response)
        except ValidationError as e:
            raise ValidationError("API returned an invalid test list") from e

    async def get_questionnaire(self, questionnaire_id: int) -> Questionnaire:
        response = self._get_json(f"{self._url}/{questionnaire_id}")
        try:
            return Questionnaire.model_validate(response)
        except ValidationError as e:
            raise ValidationError("API returned an invalid test list") from e

    async def _get_json(
        self,
        endpoint: str,
        *,
        questionnaire_id: int | None = None,
    ) -> object:
        url = f"{self._url}/{endpoint}"
        async with self._session.get(url) as response:
            try:
                self._check_status_code(response.status, questionnaire_id)
            except TimeoutError as e:
                raise ApiUnavailableError(
                    url,
                    response.status,
                    extra_message="Questionnaire API request timed out",
                ) from e
            except aiohttp.ClientError as e:
                raise ApiUnavailableError(
                    url,
                    response.status,
                    extra_message="Failed to connect to Questionnaire API",
                ) from e
            else:
                return await response.json()

    @staticmethod
    def _check_status_code(status: int, url: str, questionnaire_id: int | None) -> None:
        if status == 404 and questionnaire_id is not None:
            raise ApiNotFoundError(
                url, status, extra_message=f"Questionnaire {questionnaire_id}"
            )

        if status >= 500:
            raise ApiUnavailableError(url, status, extra_message="Questionnaire API.")

        if status != 200:
            raise ApiClientError(
                url, status, extra_message="Unexpected Questionnaire API."
            )
