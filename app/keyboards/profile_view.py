from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить профиль", callback_data="profile:edit")]
        ]
    )
