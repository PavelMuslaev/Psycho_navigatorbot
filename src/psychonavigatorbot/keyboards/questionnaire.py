from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from psychonavigatorbot.callbacks.tests import (
    AnswerCallback,
    AttemptCallback,
    TestAction,
)
from psychonavigatorbot.models.attempt import QuestionnaireAttempt


def cancel_button(attempt: QuestionnaireAttempt) -> InlineKeyboardMarkup:
    return InlineKeyboardButton(
        text="Прервать тест",
        callback_data=AttemptCallback(
            action=TestAction.CANCEL,
            test_id=attempt.test_id,
            attempt_id=attempt.attempt_id,
        ).pack(),
    )


def create_question_keyboard(
    attempt: QuestionnaireAttempt,
) -> InlineKeyboardMarkup:
    question = attempt.questions[attempt.current_index]
    rows = [
        [
            InlineKeyboardButton(
                text=f"{option.value} - {option.label}",
                callback_data=AnswerCallback(
                    attempt_id=attempt.attempt_id,
                    test_id=attempt.test_id,
                    question_id=question.id,
                    value=option.value,
                ).pack(),
            )
        ]
        for option in attempt.answer_scale
    ]

    rows.append([cancel_button(attempt)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def create_result_keyboard(
    attempt: QuestionnaireAttempt,
    *,
    retry: bool = False,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Повторить расчёт" if retry else "Рассчитать результат",
                    callback_data=AttemptCallback(
                        action=TestAction.SUBMIT,
                        test_id=attempt.test_id,
                        attempt_id=attempt.attempt_id,
                    ).pack(),
                ),
                [cancel_button(attempt)],
            ]
        ]
    )
