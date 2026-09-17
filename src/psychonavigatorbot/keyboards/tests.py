from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from psychonavigatorbot.callbacks.tests import TestAction, TestCallback, AnswerCallback
from psychonavigatorbot.models.test import TestSummary, AnswerOption


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


def create_question_keyboard(
    test_id: int, question_id: int, answer_scale: list[AnswerOption]
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{option.value} - {option.label}",
                callback_data=AnswerCallback(
                    test_id=test_id,
                    question_id=question_id,
                    value=option.value,
                ).pack(),
            )
        ]
        for option in answer_scale
    ]

    rows.append(
        [
            InlineKeyboardButton(
                text="Прервать тест",
                callback_data=TestCallback(
                    test_id=test_id,
                    action=TestAction.CANCEL,
                ).pack(),
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
