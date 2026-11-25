from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def create_inline_markup(command: dict[str, str | int]) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(text), callback_data=str(cmd))]
            for text, cmd in command.items()
        ]
    )

    return markup
