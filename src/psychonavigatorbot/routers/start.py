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
        "Тут пока пусто 👷‍♂️🚧👷": "void",
        "Тут пока пусто 👷‍♂️🚧👷2": "void",
        "Тут пока пусто 👷‍♂️🚧👷3": "void",
        "Тут пока пусто 👷‍♂️🚧👷4": "void",
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
