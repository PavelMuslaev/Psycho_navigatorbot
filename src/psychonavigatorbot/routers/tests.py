import logging
from html import escape

from aiogram import Router, F
from aiogram.types import CallbackQuery

from psychonavigatorbot.exceptions.tests import (
    ApiClientError,
    ApiContractError,
    ApiUnavailableError,
)
from psychonavigatorbot.services.tests_api import QuestionnaireApiClient
from psychonavigatorbot.models.test import TestSummary
from psychonavigatorbot.keyboards.builders import create_inline_markup


# __name__ будет содержать имя модуля: psychonavigatorbot.routers.tests
logger = logging.getLogger(__name__)

router = Router()


def format_message_tests(tests: list[TestSummary]) -> str:
    text = "<b>✨ Доступные тесты</b>\n<i>Выбирай, что проходить первым:</i>\n"

    for number, test in enumerate(tests, 1):
        text += (
            f"\n👁️ <b>{number}. {escape(test.name)}</b>\n"
            f"└ <i>{escape(test.description)}</i>\n"
        )

    text += "\n<b>👇 Выберите нужный тест ниже</b>"

    return text


@router.callback_query(F.data == "tests")
async def display_tests(cq: CallbackQuery, api_client: QuestionnaireApiClient) -> None:
    await cq.answer()

    try:
        tests = await api_client.get_tests()
    except ApiUnavailableError as error:
        logger.warning("Failed to load tests %s", error, exc_info=True)

        await cq.message.answer("Сервис тестов временно недоступен. Попробуйте позже.")
        return
    except ApiContractError as error:
        logger.exception("Questionnaire API returned an invalid tests list: %s", error)

        await cq.message.answer(
            "Не удалось обработать данные тестов. Попробуйте позже."
        )
        return
    except ApiClientError as error:
        logger.exception(
            "Unexpected Questionnaire API error while loading tests: %s ",
            error,
        )

        await cq.message.answer("Не удалось загрузить список тестов. Попробуйте позже.")
        return

    if not tests:
        logger.info("Questionnaire API returned an empty test list")

        await cq.message.answer("Сейчас нет доступных тестов.")
        return

    text = format_message_tests(tests)
    commands = create_inline_markup(
        {test.name: test.id for test in tests},
    )

    await cq.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=commands,
    )
