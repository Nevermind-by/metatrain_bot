from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.i18n import t


def main_menu_texts(lang: str = "en") -> dict[str, str]:
    return {
        "food": t("menu_food", lang),
        "workout": t("menu_workout", lang),
        "weight": t("menu_weight", lang),
        "progress": t("menu_progress", lang),
        "dashboard": t("menu_dashboard", lang),
        "profile": t("menu_profile", lang),
    }


def main_menu_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    texts = main_menu_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts["food"]), KeyboardButton(text=texts["workout"])],
            [KeyboardButton(text=texts["weight"]), KeyboardButton(text=texts["progress"])],
            [KeyboardButton(text=texts["dashboard"]), KeyboardButton(text=texts["profile"])],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=t("menu_placeholder", lang),
    )
