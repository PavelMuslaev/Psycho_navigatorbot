from uuid import UUID
import json
from typing import Literal

import aiohttp
from pydantic import TypeAdapter, ValidationError

from psychonavigatorbot.exceptions.tests import (
    ApiClientError,
    ApiContractError,
    ApiUnavailableError,
    ApiNotFoundError,
    ApiRequestRejectedError,
)
from psychonavigatorbot.models.test import Questionnaire, TestSummary
from psychonavigatorbot.models.test_results import (
    EpiResult,
    AttemptSummary,
    SavedAttempt,
    AnswerSubmission,
    QuestionnaireResult,
    QuestionnaireResultRequest,
)

TEST_ADAPTER = TypeAdapter(list[TestSummary])


class QuestionnaireApiClient:
    def __init__(
        self, base_url: str, session: aiohttp.ClientSession, history_token: str = ""
    ):
        self._url = base_url.rstrip("/")
        self._session = session
        self._history_token = history_token

    async def get_tests(self) -> list[TestSummary]:
        url = f"{self._url}/tests"
        response = await self._get_json("GET", url)
        try:
            return TEST_ADAPTER.validate_python(response)
        except ValidationError as e:
            raise ApiContractError(
                url, extra_message="API returned an invalid test list"
            ) from e

    async def get_questionnaire(self, questionnaire_id: int) -> Questionnaire:
        url = f"{self._url}/tests/{questionnaire_id}"
        response = await self._get_json("GET", url, questionnaire_id=questionnaire_id)
        try:
            questionnaire = Questionnaire.model_validate(response)
            if questionnaire.id != questionnaire_id:
                raise ApiContractError(url, extra_message="Questionnaire ID mismatch")
            return questionnaire
        except ValidationError as e:
            raise ApiContractError(
                url,
                extra_message="API returned an invalid questionnaire",
            ) from e

    async def calculate_result(
        self, test_id: int, answers: list[AnswerSubmission]
    ) -> QuestionnaireResult | EpiResult:
        url = f"{self._url}/tests/{test_id}/results"
        request = QuestionnaireResultRequest(answers=answers)
        response = await self._get_json(
            "POST",
            url,
            questionnaire_id=test_id,
            payload=request.model_dump(mode="json"),
        )
        try:
            model = EpiResult if test_id == 2 else QuestionnaireResult
            result = model.model_validate(response)
        except ValidationError as error:
            raise ApiContractError(
                url, extra_message="API returned an invalid result"
            ) from error
        else:
            if result.test_id != test_id:
                raise ApiContractError(url, extra_message="Result test ID mismatch")
            return result

    async def _history(self, method, path, adapter, payload=None):
        url = f"{self._url}/users/{path}"
        data = await self._get_json(
            method,
            url,
            payload=payload,
            headers={"Authorization": f"Bearer {self._history_token}"},
        )
        try:
            return adapter.validate_python(data)
        except ValidationError as error:
            raise ApiContractError(
                url, extra_message="Invalid attempt history"
            ) from error

    async def save_result(
        self, telegram_id: int, answers: list[AnswerSubmission], attempt_id: str, *, test_id: int = 1
    ):
        payload = QuestionnaireResultRequest(answers=answers).model_dump(mode="json")
        saved = await self._history(
            "POST",
            f"{telegram_id}/attempts/{attempt_id}?test_id={test_id}",
            TypeAdapter(SavedAttempt),
            payload,
        )
        if saved.attempt_id != UUID(attempt_id) or saved.profile.test_id != test_id:
            raise ApiContractError(self._url, extra_message="Saved attempt mismatch")
        return saved.profile

    async def get_history(self, telegram_id: int) -> list[AttemptSummary]:
        return await self._history(
            "GET", f"{telegram_id}/attempts", TypeAdapter(list[AttemptSummary])
        )

    async def get_attempt(self, telegram_id: int, attempt_id: UUID) -> SavedAttempt:
        saved = await self._history(
            "GET", f"{telegram_id}/attempts/{attempt_id}", TypeAdapter(SavedAttempt)
        )
        if saved.attempt_id != attempt_id:
            raise ApiContractError(self._url, extra_message="Saved attempt mismatch")
        return saved

    async def _get_json(
        self,
        method: Literal["GET", "POST"],
        url: str,
        *,
        questionnaire_id: int | None = None,
        headers: dict[str, str] | None = None,
        payload: dict[str, object] | None = None,
    ) -> object:
        try:
            async with self._session.request(
                method, url, json=payload, headers=headers
            ) as response:
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
                    UnicodeDecodeError,
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

        if status in (400, 422):
            raise ApiRequestRejectedError(url, status=status)

        if status >= 500:
            raise ApiUnavailableError(
                url, status=status, extra_message="Questionnaire API."
            )

        if status != 200:
            raise ApiClientError(
                url, status=status, extra_message="Unexpected Questionnaire API."
            )
