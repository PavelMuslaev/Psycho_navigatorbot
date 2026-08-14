import json
import aiohttp
from pydantic import TypeAdapter, ValidationError

from psychonavigatorbot.exceptions.tests import (
    ApiClientError,
    ApiContractError,
    ApiUnavailableError,
    ApiNotFoundError,
)
from psychonavigatorbot.models.test import Questionnaire, TestSummary

TEST_ADAPTER = TypeAdapter(list[TestSummary])


class QuestionnaireApiClient:
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self._url = base_url.rstrip("/")
        self._session = session

    async def get_tests(self) -> list[TestSummary]:
        url = f"{self._url}/tests"
        response = await self._get_json(url)
        try:
            return TEST_ADAPTER.validate_python(response)
        except ValidationError as e:
            raise ApiContractError(
                url, extra_message="API returned an invalid test list"
            ) from e

    async def get_questionnaire(self, questionnaire_id: int) -> Questionnaire:
        url = f"{self._url}/tests/{questionnaire_id}"
        response = await self._get_json(url, questionnaire_id=questionnaire_id)
        try:
            return Questionnaire.model_validate(response)
        except ValidationError as e:
            raise ApiContractError(
                url,
                extra_message="API returned an invalid questionnaire",
            ) from e

    async def _get_json(
        self,
        url: str,
        *,
        questionnaire_id: int | None = None,
    ) -> object:
        try:
            async with self._session.get(url) as response:
                self._check_status_code(
                    response.status,
                    url,
                    questionnaire_id,
                )

                try:
                    return await response.json()
                except (
                    aiohttp.ContentTypeError,
                    json.JSONDecodeError,
                ) as error:
                    raise ApiContractError(
                        url,
                        status=response.status,
                        extra_message="API returned invalid JSON",
                    ) from error
        except TimeoutError as e:
            raise ApiUnavailableError(
                url,
                extra_message="Questionnaire API request timed out",
            ) from e
        except aiohttp.ClientError as e:
            raise ApiUnavailableError(
                url,
                extra_message="Failed to connect to Questionnaire API",
            ) from e

    @staticmethod
    def _check_status_code(status: int, url: str, questionnaire_id: int | None) -> None:
        if status == 404 and questionnaire_id is not None:
            raise ApiNotFoundError(
                url, status=status, extra_message=f"Questionnaire {questionnaire_id}"
            )

        if status >= 500:
            raise ApiUnavailableError(
                url, status=status, extra_message="Questionnaire API."
            )

        if status != 200:
            raise ApiClientError(
                url, status=status, extra_message="Unexpected Questionnaire API."
            )
