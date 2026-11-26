from datetime import UTC
from html import escape
from uuid import UUID
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from psychonavigatorbot.services.tests_api import QuestionnaireApiClient
from psychonavigatorbot.exceptions.tests import ApiClientError
from psychonavigatorbot.views.questionnaire import format_result
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
)

from psychonavigatorbot.keyboards.builders import create_inline_markup

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    start_cmds = {
        "Список тестов 📝": "tests",
        "Моя история": "history",
    }

    await message.answer(
        f"Привет, <b>{message.from_user.full_name}!</b>\nЭто ПсихоНавигатор 🤓!\n\n"
        f"<b><i>Список команд: \n</i></b>",
        parse_mode="HTML",
        reply_markup=create_inline_markup(start_cmds),
    )


@router.callback_query(F.data == "void")
async def display_void(cq: CallbackQuery):
    await cq.message.answer(
        "Технические работы👷🚧👷‍♂️.\nУважаемый(ая), мы всё исправим!\n"
    )
    await cq.answer()


@router.callback_query(F.data == "history")
async def show_history(cq: CallbackQuery, api_client: QuestionnaireApiClient):
    await cq.answer()
    if not isinstance(cq.message, Message):
        return
    if cq.message.chat.type != "private":
        await cq.message.answer("Откройте историю в личном чате с ботом.")
        return
    try:
        rows = await api_client.get_history(cq.from_user.id)
    except ApiClientError:
        await cq.message.answer("Не удалось загрузить историю. Попробуйте ещё раз.")
        return
    if not rows:
        await cq.message.answer("История пока пуста.")
        return
    blocks = ["Последние прохождения"]
    buttons = []
    for number, row in enumerate(rows, start=1):
        date = row.completed_at.astimezone(UTC)
        blocks.append(f"<b>№{number} · {escape(row.test_name)}</b>\n{date:%d.%m.%Y · %H:%M} UTC")
        buttons.append([InlineKeyboardButton(text=f"Открыть №{number}", callback_data=f"saved:{row.attempt_id}")])
    await cq.message.answer(
        "\n\n".join(blocks), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith("saved:"))
async def show_saved(cq: CallbackQuery, api_client: QuestionnaireApiClient):
    await cq.answer()
    if not isinstance(cq.message, Message) or cq.message.chat.type != "private":
        return
    try:
        saved = await api_client.get_attempt(
            cq.from_user.id, UUID(cq.data.removeprefix("saved:"))
        )
    except ValueError, ApiClientError:
        await cq.message.answer(
            "Не удалось открыть прохождение. Откройте историю ещё раз."
        )
        return
    await cq.message.answer(
        format_result(saved.test_name, saved.profile), parse_mode="HTML"
    )
