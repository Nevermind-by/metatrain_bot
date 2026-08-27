from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def meal_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍳 Завтрак", callback_data="food:meal:breakfast")],
        [InlineKeyboardButton(text="🍲 Обед", callback_data="food:meal:lunch")],
        [InlineKeyboardButton(text="🍽 Ужин", callback_data="food:meal:dinner")],
        [InlineKeyboardButton(text="🍎 Перекус", callback_data="food:meal:snack")],
    ])
