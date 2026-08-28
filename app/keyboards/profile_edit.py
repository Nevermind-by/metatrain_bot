from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def edit_profile_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("gender", lang), callback_data="profile:edit:gender")],
            [InlineKeyboardButton(text=t("age", lang), callback_data="profile:edit:age")],
            [InlineKeyboardButton(text=t("height", lang), callback_data="profile:edit:height")],
            [InlineKeyboardButton(text=t("weight", lang), callback_data="profile:edit:weight")],
            [InlineKeyboardButton(text=t("activity", lang), callback_data="profile:edit:activity")],
            [InlineKeyboardButton(text=t("goal", lang), callback_data="profile:edit:goal")],
            [InlineKeyboardButton(text=t("profile", lang), callback_data="profile:show")],
            [InlineKeyboardButton(text=t("dashboard", lang), callback_data="dashboard:home")],
        ]
    )
