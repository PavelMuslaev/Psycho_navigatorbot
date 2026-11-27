from dataclasses import dataclass
from secrets import token_urlsafe
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


PAGE_SIZE = 5


@router.callback_query(F.data == "history")
@router.callback_query(F.data.regexp(r"^history:[0-9]{1,9}$"))
async def show_history(cq: CallbackQuery, api_client: QuestionnaireApiClient):
    await cq.answer()
    if not isinstance(cq.message, Message):
        return
    if cq.message.chat.type != "private":
        await cq.message.answer("Откройте историю в личном чате с ботом.")
        return
    paging = (cq.data or "").startswith("history:")
    offset = int(cq.data.split(":")[1]) if paging else 0
    send = cq.message.edit_text if paging else cq.message.answer
    await render_history(cq, api_client, offset, send)


async def render_history(cq, api_client, offset, send):
    async def load(start):
        return await api_client.get_history(
            cq.from_user.id, limit=PAGE_SIZE + 1, offset=start
        )

    try:
        rows = await load(offset)
        if offset and not rows:
            # Find the last nonempty page if the list shrank since it was displayed.
            low, high = 0, offset // PAGE_SIZE
            while low < high:
                middle = (low + high) // 2
                if await load(middle * PAGE_SIZE):
                    low = middle + 1
                else:
                    high = middle
            offset = max(0, low - 1) * PAGE_SIZE
            rows = await load(offset)
    except ApiClientError:
        await cq.message.answer("Не удалось загрузить историю. Попробуйте ещё раз.")
        return
    if not rows:
        await send("История пока пуста.")
        return
    blocks = ["Последние прохождения"]
    buttons = []
    for number, row in enumerate(rows[:PAGE_SIZE], start=offset + 1):
        date = row.completed_at.astimezone(UTC)
        blocks.append(
            f"<b>№{number} · {escape(row.test_name)}</b>\n{date:%d.%m.%Y · %H:%M} UTC"
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Открыть №{number}",
                    callback_data=record_callback("saved", row.attempt_id, offset),
                )
            ]
        )
    navigation = []
    if offset:
        navigation.append(
            InlineKeyboardButton(
                text="Назад", callback_data=f"history:{max(0, offset - PAGE_SIZE)}"
            )
        )
    if len(rows) > PAGE_SIZE:
        navigation.append(
            InlineKeyboardButton(
                text="Далее", callback_data=f"history:{offset + PAGE_SIZE}"
            )
        )
    if navigation:
        buttons.append(navigation)
    await send(
        "\n\n".join(blocks),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("saved:"))
async def show_saved(cq: CallbackQuery, api_client: QuestionnaireApiClient):
    await cq.answer()
    if not isinstance(cq.message, Message) or cq.message.chat.type != "private":
        return
    try:
        attempt_id, offset = parse_record(cq.data)
        saved = await api_client.get_attempt(cq.from_user.id, attempt_id)
    except ValueError, ApiClientError:
        await cq.message.answer(
            "Не удалось открыть прохождение. Откройте историю ещё раз."
        )
        return
    await cq.message.answer(
        format_result(saved.test_name, saved.profile),
        parse_mode="HTML",
        reply_markup=create_inline_markup(
            {"Удалить из истории": record_callback("remove", saved.attempt_id, offset)}
        ),
    )


def record_callback(action, attempt_id, offset):
    return f"{action}:{attempt_id}:{offset}" if offset else f"{action}:{attempt_id}"


def parse_record(data):
    _, raw_id, *page = data.split(":")
    if page and (
        len(page) != 1
        or not page[0].isascii()
        or not page[0].isdigit()
        or len(page[0]) > 9
    ):
        raise ValueError("Invalid history offset")
    return UUID(raw_id), int(page[0]) if page else 0


@dataclass(frozen=True)
class Confirmation:
    message_id: int
    attempt_id: UUID
    offset: int
    token: str


# The polling dispatcher serializes updates per user with SimpleEventIsolation.
# Only the most recently opened confirmation for that user is actionable.
pending: dict[int, Confirmation] = {}


@router.callback_query(F.data.regexp(r"^(remove|keep|erase):"))
async def manage_saved(cq: CallbackQuery, api_client: QuestionnaireApiClient):
    if not isinstance(cq.message, Message) or cq.message.chat.type != "private":
        await cq.answer()
        return
    owner = cq.from_user.id
    action, value = cq.data.split(":", 1)
    if action == "remove":
        try:
            attempt_id, offset = parse_record(cq.data)
        except ValueError:
            await cq.answer("Некорректная кнопка.")
            return
        token = token_urlsafe(16)
        markup = create_inline_markup(
            {"Подтвердить удаление": f"erase:{token}", "Отмена": f"keep:{token}"}
        )
        await cq.message.edit_reply_markup(reply_markup=markup)
        pending[owner] = Confirmation(cq.message.message_id, attempt_id, offset, token)
        await cq.answer()
        return

    active = pending.get(owner)
    if (
        not active
        or active.message_id != cq.message.message_id
        or active.token != value
    ):
        await cq.answer("Подтверждение больше не действует.")
        return
    del pending[owner]
    if action == "keep":
        markup = create_inline_markup(
            {
                "Удалить из истории": record_callback(
                    "remove", active.attempt_id, active.offset
                )
            }
        )
        await cq.message.edit_reply_markup(reply_markup=markup)
        await cq.answer()
        return
    try:
        await api_client.delete_attempt(owner, active.attempt_id)
    except ApiClientError as error:
        if error.status != 404:
            pending.setdefault(owner, active)
            await cq.answer("Не удалось удалить. Попробуйте ещё раз.", show_alert=True)
            return
    await cq.answer("Запись удалена из истории.")
    await cq.message.edit_text(
        "Запись удалена из истории.",
        reply_markup=create_inline_markup(
            {"Вернуться в историю": f"history:{active.offset}"}
        ),
    )
    await render_history(cq, api_client, active.offset, cq.message.edit_text)
