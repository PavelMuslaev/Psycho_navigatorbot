from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class TestAction(StrEnum):
    OPEN = "open"
    START = "start"


class TestCallback(CallbackData, prefix="test"):
    action: TestAction
    test_id: int
