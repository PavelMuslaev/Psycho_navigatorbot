import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from pydantic import ValidationError

from psychonavigatorbot.callbacks.tests import (
    AnswerCallback,
    AttemptCallback,
    TestAction,
    TestCallback,
)
from psychonavigatorbot.exceptions.tests import (
    ApiClientError,
    ApiContractError,
    ApiNotFoundError,
    ApiRequestRejectedError,
    ApiUnavailableError,
)
from psychonavigatorbot.keyboards.questionnaire import (
    create_question_keyboard,
    create_result_keyboard,
)
from psychonavigatorbot.models.attempt import QuestionnaireAttempt
from psychonavigatorbot.models.test_results import AnswerSubmission
from psychonavigatorbot.services.tests_api import QuestionnaireApiClient
from psychonavigatorbot.states.questionnaire import QuestionnaireState
from psychonavigatorbot.views.questionnaire import (
    format_question,
    format_ready,
    format_result,
)


logger = logging.getLogger(__name__)
router = Router(name="questionnaire")


async def save_attempt(
    state: FSMContext,
    attempt: QuestionnaireAttempt,
) -> None:
    await state.set_data(attempt.model_dump(mode="json"))


async def load_attempt(
    cq: CallbackQuery,
    state: FSMContext,
    callback_data: AnswerCallback | AttemptCallback,
) -> QuestionnaireAttempt | None:
    if not isinstance(cq.message, Message):
        await cq.answer("Сообщение недоступно. Используйте /cancel.")
        return None

    try:
        attempt = QuestionnaireAttempt.model_validate(await state.get_data())
    except ValueError:
        # Не выводим ValidationError: он может содержать ответы пользователя.
        logger.error(
            "Invalid FSM data: user_id=%s",
            cq.from_user.id,
        )

        await state.clear()
        await cq.answer(
            "Прохождение не найдено. Начните тест заново.",
        )
        return None

    if (
        callback_data.test_id != attempt.test_id
        or callback_data.attempt_id != attempt.attempt_id
        or cq.message.message_id != attempt.message_id
    ):
        await cq.answer(
            "Эта кнопка относится к другому прохождению.",
        )
        return None

    return attempt


async def edit_screen(
    message: Message,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    try:
        await message.edit_text(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as error:
        # Повторно показывать уже установленный экран безопасно.
        if "message is not modified" not in error.message.lower():
            raise


async def show_attempt(
    message: Message,
    attempt: QuestionnaireAttempt,
) -> None:
    if attempt.is_complete:
        text = format_ready(attempt)
        keyboard = create_result_keyboard(attempt)
    else:
        text = format_question(attempt)
        keyboard = create_question_keyboard(attempt)

    await edit_screen(
        message,
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.callback_query(
    StateFilter(None),
    TestCallback.filter(F.action == TestAction.START),
)
async def start_questionnaire(
    cq: CallbackQuery,
    callback_data: TestCallback,
    state: FSMContext,
    api_client: QuestionnaireApiClient,
) -> None:
    if not isinstance(cq.message, Message):
        await cq.answer(
            "Сообщение недоступно. Откройте список тестов заново.",
        )
        return

    await cq.answer()

    try:
        questionnaire = await api_client.get_questionnaire(
            callback_data.test_id,
        )

        attempt = QuestionnaireAttempt(
            test_id=questionnaire.id,
            message_id=cq.message.message_id,
            questionnaire_name=questionnaire.name,
            questions=questionnaire.questions,
            answer_scale=questionnaire.answer_scale,
        )

    except (ApiClientError, ValidationError) as error:
        logger.warning(
            "Start failed: user_id=%s test_id=%s error_type=%s",
            cq.from_user.id,
            callback_data.test_id,
            type(error).__name__,
        )

        await cq.message.answer(
            "Не удалось начать тест. Попробуйте позже.",
        )
        return

    # Сначала убеждаемся, что Telegram принял первый вопрос.
    await show_attempt(cq.message, attempt)

    await save_attempt(state, attempt)
    await state.set_state(QuestionnaireState.answering)

    logger.info(
        "Attempt started: user_id=%s test_id=%s",
        cq.from_user.id,
        attempt.test_id,
    )


@router.callback_query(
    TestCallback.filter(F.action == TestAction.START),
)
async def reject_second_start(
    cq: CallbackQuery,
) -> None:
    await cq.answer(
        "Сначала завершите текущий тест или отмените его через /cancel.",
    )


@router.callback_query(
    QuestionnaireState.answering,
    AnswerCallback.filter(),
)
async def answer_question(
    cq: CallbackQuery,
    callback_data: AnswerCallback,
    state: FSMContext,
    api_client: QuestionnaireApiClient,
) -> None:
    attempt = await load_attempt(
        cq,
        state,
        callback_data,
    )

    if attempt is None:
        return

    if attempt.is_complete:
        await cq.answer(
            "Все ответы уже собраны.",
        )
        return

    question = attempt.questions[attempt.current_index]

    if callback_data.question_id != question.id:
        await cq.answer(
            "Этот вопрос уже обработан.",
        )

        # Если предыдущее редактирование не дошло до Telegram,
        # восстановим экран.
        await show_attempt(
            cq.message,
            attempt,
        )
        return

    if callback_data.value not in {option.value for option in attempt.answer_scale}:
        await cq.answer(
            "Недопустимый вариант ответа.",
        )
        return

    await cq.answer()

    attempt.answers.append(
        AnswerSubmission(
            question_id=question.id,
            value=callback_data.value,
        )
    )

    attempt.current_index += 1

    await save_attempt(
        state,
        attempt,
    )

    if attempt.is_complete:
        await state.set_state(
            QuestionnaireState.ready_to_submit,
        )
        await calculate_and_display(cq, state, attempt, api_client)
        return

    await show_attempt(
        cq.message,
        attempt,
    )


@router.callback_query(
    QuestionnaireState.ready_to_submit,
    AttemptCallback.filter(F.action == TestAction.SUBMIT),
)
async def submit_result(
    cq: CallbackQuery,
    callback_data: AttemptCallback,
    state: FSMContext,
    api_client: QuestionnaireApiClient,
) -> None:
    attempt = await load_attempt(
        cq,
        state,
        callback_data,
    )

    if attempt is None:
        return

    if not attempt.is_complete:
        await cq.answer(
            "Сначала ответьте на все вопросы.",
        )
        return

    await cq.answer(
        "Рассчитываю результат…",
    )

    await calculate_and_display(cq, state, attempt, api_client)


async def calculate_and_display(
    cq: CallbackQuery,
    state: FSMContext,
    attempt: QuestionnaireAttempt,
    api_client: QuestionnaireApiClient,
) -> None:
    await state.set_state(
        QuestionnaireState.submitting,
    )

    try:
        try:
            result = await api_client.save_result(
                cq.from_user.id,
                attempt.answers,
                attempt.attempt_id,
            )

        except ApiClientError as error:
            logger.warning(
                "Calculation failed: user_id=%s test_id=%s error_type=%s status=%s",
                cq.from_user.id,
                attempt.test_id,
                type(error).__name__,
                error.status,
            )

            if isinstance(
                error,
                ApiUnavailableError,
            ):
                text = (
                    "Сервис временно недоступен. Ответы сохранены. Попробуйте ещё раз."
                )

            elif isinstance(
                error,
                ApiRequestRejectedError,
            ):
                text = (
                    "Сервис отклонил ответы. "
                    "Они сохранены. "
                    "Если ошибка повторится, "
                    "отмените прохождение "
                    "и начните заново."
                )

            elif isinstance(
                error,
                ApiNotFoundError,
            ):
                text = "Расчёт этого теста сейчас недоступен. Ответы сохранены."

            elif isinstance(
                error,
                ApiContractError,
            ):
                text = "Не удалось обработать результат сервиса. Ответы сохранены."

            else:
                text = "Не удалось рассчитать результат. Ответы сохранены."

            await edit_screen(
                cq.message,
                text,
                reply_markup=create_result_keyboard(
                    attempt,
                    retry=True,
                ),
            )
            return

        # Очищаем прогресс только после успешной отправки
        # результата в Telegram.
        await edit_screen(
            cq.message,
            format_result(
                attempt.questionnaire_name,
                result,
            ),
            parse_mode="HTML",
            reply_markup=None,
        )

        await state.clear()

        logger.info(
            "Attempt completed: user_id=%s test_id=%s",
            cq.from_user.id,
            attempt.test_id,
        )

    finally:
        # В том числе при ошибке Telegram или отмене coroutine
        # не оставляем пользователя навсегда в submitting.
        # Собранные ответы остаются в storage.
        if await state.get_state() == QuestionnaireState.submitting.state:
            await state.set_state(
                QuestionnaireState.ready_to_submit,
            )


@router.callback_query(
    StateFilter(
        QuestionnaireState.answering,
        QuestionnaireState.ready_to_submit,
    ),
    AttemptCallback.filter(F.action == TestAction.CANCEL),
)
async def cancel_questionnaire(
    cq: CallbackQuery,
    callback_data: AttemptCallback,
    state: FSMContext,
) -> None:
    attempt = await load_attempt(
        cq,
        state,
        callback_data,
    )

    if attempt is None:
        return

    await cq.answer()
    await state.clear()

    await cq.message.edit_text(
        "Прохождение отменено. Несохранённые ответы удалены.",
    )

    logger.info(
        "Attempt cancelled: user_id=%s test_id=%s",
        cq.from_user.id,
        attempt.test_id,
    )


@router.message(
    Command("cancel"),
)
async def cancel_by_command(
    message: Message,
    state: FSMContext,
) -> None:
    if await state.get_state() is None:
        await message.answer(
            "Активного прохождения нет.",
        )
        return

    await state.clear()

    await message.answer(
        "Прохождение отменено. Несохранённые ответы удалены.",
    )

    logger.info(
        "Attempt cancelled by command: chat_id=%s",
        message.chat.id,
    )


# Регистрируется после основного обработчика ответа:
# восстанавливает экран «Рассчитать»,
# если последний edit_text не дошёл до Telegram.
@router.callback_query(
    QuestionnaireState.ready_to_submit,
    AnswerCallback.filter(),
)
async def answer_after_completion(
    cq: CallbackQuery,
    callback_data: AnswerCallback,
    state: FSMContext,
) -> None:
    attempt = await load_attempt(
        cq,
        state,
        callback_data,
    )

    if attempt is None:
        return

    await cq.answer(
        "Все ответы уже собраны.",
    )

    await show_attempt(
        cq.message,
        attempt,
    )


# Последний обработчик:
# кнопки после отмены/перезапуска
# или неверного формата.
@router.callback_query(F.data.startswith("answer:") | F.data.startswith("attempt:"))
async def stale_button(
    cq: CallbackQuery,
) -> None:
    await cq.answer(
        "Эта кнопка больше не действует. Откройте тест заново.",
    )
