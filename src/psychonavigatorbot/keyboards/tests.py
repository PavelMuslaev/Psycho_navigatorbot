from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from psychonavigatorbot.callbacks.tests import TestAction, TestCallback
from psychonavigatorbot.models.test import TestSummary


def create_test_list_keyboard(
    tests: list[TestSummary],
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=test.name,
                    callback_data=TestCallback(
                        action=TestAction.OPEN,
                        test_id=test.id,
                    ).pack(),
                )
            ]
            for test in tests
        ]
    )


def create_start_test_keyboard(
    test_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Начать тест ▶️",
                    callback_data=TestCallback(
                        action=TestAction.START,
                        test_id=test_id,
                    ).pack(),
                )
            ]
        ]
    )
