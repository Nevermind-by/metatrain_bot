from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def dashboard_keyboard(lang: str = "en", active_workout: bool = False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("menu_food", lang), callback_data="dashboard:food"),
                InlineKeyboardButton(text=("▶️ Продолжить тренировку" if lang == "ru" else "▶️ Continue workout") if active_workout else t("menu_workout", lang), callback_data="workout:current" if active_workout else "dashboard:workout"),
            ],
            [
                InlineKeyboardButton(text=t("menu_weight", lang), callback_data="dashboard:weight"),
                InlineKeyboardButton(text=t("menu_progress", lang), callback_data="dashboard:progress"),
            ],
            [InlineKeyboardButton(text=t("menu_profile", lang), callback_data="dashboard:profile")],
            [InlineKeyboardButton(text=t("refresh", lang), callback_data="dashboard:refresh")],
        ]
    )
