from psychonavigatorbot.models.test import TestSummary, Questionnaire

from html import escape


def format_tests(tests: list[TestSummary]) -> str:
    text = "<b>✨ Доступные тесты</b>\n<i>Выбирай, что проходить первым:</i>\n"

    for number, test in enumerate(tests, 1):
        text += (
            f"\n👁️ <b>{number}. {escape(test.name)}</b>\n"
            f"└ <i>{escape(test.description)}</i>\n"
        )

    text += "\n<b>👇 Выберите нужный тест ниже</b>"

    return text


def format_questionnaire(
    questionnaire: Questionnaire,
) -> str:
    return (
        f"🧠 <b>{escape(questionnaire.name)}</b>\n\n"
        f"{escape(questionnaire.description)}\n\n"
        "<b>Инструкция:</b>\n"
        f"{escape(questionnaire.instructions)}"
    )
