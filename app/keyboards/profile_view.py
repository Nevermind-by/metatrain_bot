from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def profile_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("edit_profile", lang), callback_data="profile:edit")],
        [InlineKeyboardButton(text=t("dashboard", lang), callback_data="dashboard:home")],
    ])
