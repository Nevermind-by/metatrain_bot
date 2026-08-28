from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def _footer(lang: str) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(text=t("profile", lang), callback_data="profile:show"),
        InlineKeyboardButton(text=t("dashboard", lang), callback_data="dashboard:home"),
    ]


def gender_edit_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("male", lang), callback_data="profile:gender:male"), InlineKeyboardButton(text=t("female", lang), callback_data="profile:gender:female")],
        _footer(lang),
    ])


def activity_edit_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("sedentary", lang), callback_data="profile:activity:sedentary")],
        [InlineKeyboardButton(text=t("light", lang), callback_data="profile:activity:light")],
        [InlineKeyboardButton(text=t("moderate", lang), callback_data="profile:activity:moderate")],
        [InlineKeyboardButton(text=t("high", lang), callback_data="profile:activity:high")],
        [InlineKeyboardButton(text=t("very_high", lang), callback_data="profile:activity:very_high")],
        _footer(lang),
    ])


def goal_edit_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("lose", lang), callback_data="profile:goal:lose")],
        [InlineKeyboardButton(text=t("maintain", lang), callback_data="profile:goal:maintain")],
        [InlineKeyboardButton(text=t("gain", lang), callback_data="profile:goal:gain")],
        _footer(lang),
    ])
