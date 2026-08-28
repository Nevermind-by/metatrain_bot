from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def meal_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    meals = {
        "ru": [("🍳 Завтрак", "breakfast"), ("🍲 Обед", "lunch"), ("🍽 Ужин", "dinner"), ("🍎 Перекус", "snack")],
        "en": [("🍳 Breakfast", "breakfast"), ("🍲 Lunch", "lunch"), ("🍽 Dinner", "dinner"), ("🍎 Snack", "snack")],
    }
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"food:meal:{value}")] for text, value in meals.get(lang, meals["en"])
    ] + [[InlineKeyboardButton(text=t("dashboard", lang), callback_data="dashboard:home")]])
