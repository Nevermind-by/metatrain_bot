from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def profile_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    edit = "✏️ Изменить профиль" if lang == "ru" else "✏️ Edit profile"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=edit, callback_data="profile:edit")],
        [InlineKeyboardButton(text=t("dashboard", lang), callback_data="dashboard:home")],
    ])
