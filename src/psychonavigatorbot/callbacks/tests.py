from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class TestAction(StrEnum):
    OPEN = "open"
    START = "start"
    SUBMIT = "submit"
    CANCEL = "cancel"


class TestCallback(CallbackData, prefix="test"):
    action: TestAction
    test_id: int


class AnswerCallback(CallbackData, prefix="answer"):
    attempt_id: str
    test_id: int
    question_id: int
    value: int


class AttemptCallback(CallbackData, prefix="attempt"):
    action: TestAction
    test_id: int
    attempt_id: str
