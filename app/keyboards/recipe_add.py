from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def recipe_add_keyboard(recipes) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"🍲 {recipe.name}", callback_data=f"food:recipe:{recipe.id}")] for recipe in recipes]
    rows.append([InlineKeyboardButton(text="➕ Новый продукт", callback_data="food:product:new")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
