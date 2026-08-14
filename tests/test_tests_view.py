import asyncio

import pytest

from psychonavigatorbot.callbacks import tests as test_callbacks
from psychonavigatorbot.exceptions.tests import (
    ApiClientError,
    ApiContractError,
    ApiNotFoundError,
    ApiUnavailableError,
)
from psychonavigatorbot.keyboards.tests import (
    create_start_test_keyboard,
    create_test_list_keyboard,
)
from psychonavigatorbot.models import test as test_models
from psychonavigatorbot.routers.tests import (
    display_questionnaire,
    display_tests,
    format_message_tests,
    format_questionnaire_message,
)


class FakeMessage:
    def __init__(self):
        self.answers: list[tuple[str, dict[str, object]]] = []

    async def answer(self, text: str, **kwargs):
        self.answers.append((text, kwargs))


class FakeCallbackQuery:
    def __init__(self):
        self.message = FakeMessage()
        self.answer_calls: list[str | None] = []

    async def answer(self, text: str | None = None):
        self.answer_calls.append(text)


class FailingApiClient:
    def __init__(self, error: Exception):
        self._error = error

    async def get_tests(self):
        raise self._error

    async def get_questionnaire(self, questionnaire_id: int):
        raise self._error


def test_test_list_message_escapes_api_data():
    text = format_message_tests(
        [
            test_models.TestSummary(
                id=1,
                name="<script>alert('x')</script>",
                description='Use "quoted" & unsafe <b>HTML</b>',
            )
        ]
    )

    assert "<script>" not in text
    assert "<b>HTML</b>" not in text
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in text
    assert "Use &quot;quoted&quot; &amp; unsafe &lt;b&gt;HTML&lt;/b&gt;" in text


def test_questionnaire_message_escapes_api_data():
    text = format_questionnaire_message(
        test_models.Questionnaire(
            id=1,
            name="<unsafe>",
            description="Description & details",
            instructions="Click <here>",
            answer_scale=[{"value": 1, "label": "Never"}],
            questions=[{"id": 1, "text": "Question?"}],
        )
    )

    assert "<unsafe>" not in text
    assert "Click <here>" not in text
    assert "&lt;unsafe&gt;" in text
    assert "Description &amp; details" in text
    assert "Click &lt;here&gt;" in text


def test_test_list_callback_contains_action_and_id():
    keyboard = create_test_list_keyboard(
        [
            test_models.TestSummary(
                id=42,
                name="Anxiety screening",
                description="Short screening questionnaire",
            )
        ]
    )

    callback_data = keyboard.inline_keyboard[0][0].callback_data
    assert callback_data is not None

    parsed = test_callbacks.TestCallback.unpack(callback_data)

    assert parsed.action == test_callbacks.TestAction.OPEN
    assert parsed.test_id == 42


def test_start_callback_contains_action_and_id():
    keyboard = create_start_test_keyboard(42)
    callback_data = keyboard.inline_keyboard[0][0].callback_data
    assert callback_data is not None

    parsed = test_callbacks.TestCallback.unpack(callback_data)

    assert parsed.action == test_callbacks.TestAction.START
    assert parsed.test_id == 42


@pytest.mark.parametrize(
    "error",
    [
        ApiUnavailableError(
            "https://api.example.test/tests",
            extra_message="Failed to connect to Questionnaire API",
        ),
        ApiContractError(
            "https://api.example.test/tests",
            extra_message="API returned an invalid test list",
        ),
        ApiClientError(
            "https://api.example.test/tests",
            status=400,
            extra_message="Unexpected Questionnaire API.",
        ),
    ],
)
def test_display_tests_error_messages_hide_exception_details(error):
    async def run_test():
        callback_query = FakeCallbackQuery()

        await display_tests(callback_query, FailingApiClient(error))

        message, _ = callback_query.message.answers[0]
        assert "https://api.example.test" not in message
        assert "Status code" not in message
        assert "Failed to connect" not in message
        assert "API returned" not in message

    asyncio.run(run_test())


@pytest.mark.parametrize(
    "error",
    [
        ApiNotFoundError(
            "https://api.example.test/tests/7",
            status=404,
            extra_message="Questionnaire 7",
        ),
        ApiUnavailableError(
            "https://api.example.test/tests/7",
            extra_message="request timed out",
        ),
        ApiContractError(
            "https://api.example.test/tests/7",
            extra_message="API returned an invalid questionnaire",
        ),
        ApiClientError(
            "https://api.example.test/tests/7",
            status=400,
            extra_message="Unexpected Questionnaire API.",
        ),
    ],
)
def test_display_questionnaire_error_messages_hide_exception_details(error):
    async def run_test():
        callback_query = FakeCallbackQuery()
        callback_data = test_callbacks.TestCallback(
            action=test_callbacks.TestAction.OPEN,
            test_id=7,
        )

        await display_questionnaire(
            callback_query, callback_data, FailingApiClient(error)
        )

        message, _ = callback_query.message.answers[0]
        assert "https://api.example.test" not in message
        assert "Status code" not in message
        assert "request timed out" not in message
        assert "API returned" not in message

    asyncio.run(run_test())
