from aiogram import F, Router
from aiogram.types import CallbackQuery
from html import escape

from psychonavigatorbot.services.tests_api import get_tests
from psychonavigatorbot.models.test import Test
from psychonavigatorbot.keyboards.builders import create_inline_markup

router = Router()


def format_message_tests(tests: list[Test]) -> str:
    text = "<b>✨ Доступные тесты</b>\n<i>Выбирай, что проходить первым:</i>\n"

    for number, test in enumerate(tests, 1):
        text += (
            f"\n👁️ <b>{number}. {escape(test['name'])}</b>\n"
            f"└ <i>{escape(test['description'])}</i>\n"
        )

    text += "\n<b>👇 Выберите нужный тест ниже</b>"

    return text



@router.callback_query(F.data == "tests")
async def display_tests(cq: CallbackQuery):
    try:
        tests = await get_tests()
    except Exception as err:
        await cq.message.answer(f"Ошибка при чтении данных... {err}")
    else:
        if tests is not None:
            text = format_message_tests(tests)
            commands = create_inline_markup({test["name"]: test["id"] for test in tests})
            await cq.message.answer(text, parse_mode="html", reply_markup=commands)
        else:
            await cq.message.answer(f"БЕДА!")
    finally:
        await cq.answer()
