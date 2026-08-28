from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def dashboard_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("menu_food", lang), callback_data="dashboard:food"),
                InlineKeyboardButton(text=t("menu_workout", lang), callback_data="dashboard:workout"),
            ],
            [
                InlineKeyboardButton(text=t("menu_weight", lang), callback_data="dashboard:weight"),
                InlineKeyboardButton(text=t("menu_progress", lang), callback_data="dashboard:progress"),
            ],
            [InlineKeyboardButton(text=t("menu_profile", lang), callback_data="dashboard:profile")],
            [InlineKeyboardButton(text=t("refresh", lang), callback_data="dashboard:refresh")],
        ]
    )
