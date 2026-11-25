import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from psychonavigatorbot.exceptions.tests import (
    ApiClientError,
    ApiContractError,
    ApiUnavailableError,
    ApiNotFoundError,
)
from psychonavigatorbot.services.tests_api import QuestionnaireApiClient
from psychonavigatorbot.views.tests import format_tests, format_questionnaire
from psychonavigatorbot.keyboards.tests import (
    create_test_list_keyboard,
    create_start_test_keyboard,
)
from psychonavigatorbot.callbacks.tests import TestCallback, TestAction

# __name__ будет содержать имя модуля: psychonavigatorbot.routers.tests
logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "tests")
async def display_tests(cq: CallbackQuery, api_client: QuestionnaireApiClient) -> None:
    await cq.answer()

    try:
        tests = await api_client.get_tests()
    except ApiUnavailableError as error:
        logger.warning("Failed to load tests: %s", error, exc_info=True)

        await cq.message.answer("Сервис тестов временно недоступен. Попробуйте позже.")
        return
    except ApiContractError as error:
        logger.exception("Questionnaire API returned an invalid test list: %s", error)

        await cq.message.answer(
            "Не удалось обработать данные тестов. Попробуйте позже."
        )
        return
    except ApiClientError as error:
        logger.exception(
            "Unexpected Questionnaire API error while loading tests: %s",
            error,
        )

        await cq.message.answer("Не удалось загрузить список тестов. Попробуйте позже.")
        return

    if not tests:
        logger.info("Questionnaire API returned an empty test list")

        await cq.message.answer("Сейчас нет доступных тестов.")
        return

    text = format_tests(tests)
    commands = create_test_list_keyboard(tests)

    await cq.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=commands,
    )


@router.callback_query(TestCallback.filter(F.action == TestAction.OPEN))
async def display_questionnaire(
    cq: CallbackQuery,
    callback_data: TestCallback,
    api_client: QuestionnaireApiClient,
) -> None:
    await cq.answer()

    try:
        questionnaire = await api_client.get_questionnaire(callback_data.test_id)

    except ApiNotFoundError as error:
        logger.info(
            "Questionnaire was not found: %s",
            error,
        )

        await cq.message.answer("Выбранный тест не найден. Обновите список тестов.")
        return

    except ApiUnavailableError as error:
        logger.warning(
            "Failed to load questionnaire: %s",
            error,
            exc_info=True,
        )

        await cq.message.answer("Сервис тестов временно недоступен. Попробуйте позже.")
        return

    except ApiContractError as error:
        logger.exception(
            "Questionnaire API returned invalid data: %s",
            error,
        )

        await cq.message.answer("Не удалось обработать данные теста. Попробуйте позже.")
        return

    except ApiClientError as error:
        logger.exception(
            "Unexpected API error while loading questionnaire: %s",
            error,
        )

        await cq.message.answer(
            "Не удалось загрузить выбранный тест. Попробуйте позже."
        )
        return

    text = format_questionnaire(questionnaire)
    keyboard = create_start_test_keyboard(questionnaire.id)

    await cq.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )
