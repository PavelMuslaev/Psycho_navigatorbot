import asyncio
import json

import aiohttp
import pytest

from psychonavigatorbot.exceptions.tests import (
    ApiClientError,
    ApiContractError,
    ApiNotFoundError,
    ApiUnavailableError,
)
from psychonavigatorbot.services.tests_api import QuestionnaireApiClient


class FakeResponse:
    def __init__(
        self,
        status: int,
        payload: object = None,
        json_error: Exception | None = None,
    ):
        self.status = status
        self._payload = payload
        self._json_error = json_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def json(self):
        if self._json_error is not None:
            raise self._json_error

        return self._payload


class FakeSession:
    def __init__(
        self,
        response: FakeResponse | None = None,
        error: Exception | None = None,
    ):
        self._response = response
        self._error = error
        self.requested_urls: list[str] = []

    def get(self, url: str):
        self.requested_urls.append(url)
        if self._error is not None:
            raise self._error

        return self._response


def test_get_tests_success():
    async def run_test():
        session = FakeSession(
            FakeResponse(
                200,
                [
                    {
                        "id": 1,
                        "name": "Anxiety screening",
                        "description": "Short screening questionnaire",
                    }
                ],
            )
        )
        client = QuestionnaireApiClient("https://api.example.test/", session)

        tests = await client.get_tests()

        assert session.requested_urls == ["https://api.example.test/tests"]
        assert tests[0].id == 1
        assert tests[0].name == "Anxiety screening"

    asyncio.run(run_test())


def test_get_questionnaire_success():
    async def run_test():
        session = FakeSession(
            FakeResponse(
                200,
                {
                    "id": 7,
                    "name": "Anxiety screening",
                    "description": "Short screening questionnaire",
                    "instructions": "Choose one answer per question.",
                    "answer_scale": [{"value": 1, "label": "Never"}],
                    "questions": [{"id": 1, "text": "Do you feel anxious?"}],
                },
            )
        )
        client = QuestionnaireApiClient("https://api.example.test", session)

        questionnaire = await client.get_questionnaire(7)

        assert session.requested_urls == ["https://api.example.test/tests/7"]
        assert questionnaire.id == 7
        assert questionnaire.questions[0].id == 1

    asyncio.run(run_test())


def test_get_questionnaire_404():
    async def run_test():
        client = QuestionnaireApiClient(
            "https://api.example.test",
            FakeSession(FakeResponse(404, {"detail": "Not found"})),
        )

        with pytest.raises(ApiNotFoundError) as error:
            await client.get_questionnaire(7)

        assert error.value.status == 404

    asyncio.run(run_test())


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [
        (400, ApiClientError),
        (500, ApiUnavailableError),
    ],
)
def test_get_tests_other_unsuccessful_status(status, expected_error):
    async def run_test():
        client = QuestionnaireApiClient(
            "https://api.example.test",
            FakeSession(FakeResponse(status, {"detail": "Error"})),
        )

        with pytest.raises(expected_error) as error:
            await client.get_tests()

        assert error.value.status == status

    asyncio.run(run_test())


@pytest.mark.parametrize(
    "transport_error",
    [
        TimeoutError("request timed out"),
        aiohttp.ClientConnectionError("connection refused"),
    ],
)
def test_get_tests_timeout_or_connection_error(transport_error):
    async def run_test():
        client = QuestionnaireApiClient(
            "https://api.example.test",
            FakeSession(error=transport_error),
        )

        with pytest.raises(ApiUnavailableError):
            await client.get_tests()

    asyncio.run(run_test())


def test_get_tests_invalid_json():
    async def run_test():
        client = QuestionnaireApiClient(
            "https://api.example.test",
            FakeSession(
                FakeResponse(
                    200,
                    json_error=json.JSONDecodeError("Expecting value", "not-json", 0),
                )
            ),
        )

        with pytest.raises(ApiContractError):
            await client.get_tests()

    asyncio.run(run_test())


def test_get_tests_valid_json_with_invalid_structure():
    async def run_test():
        client = QuestionnaireApiClient(
            "https://api.example.test",
            FakeSession(FakeResponse(200, {"id": 1, "name": "Not a list"})),
        )

        with pytest.raises(ApiContractError):
            await client.get_tests()

    asyncio.run(run_test())
