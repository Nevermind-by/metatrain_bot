from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.models.product import Product


def product_picker(products: list[Product]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=p.name, callback_data=f"recipe:product:{p.id}")] for p in products if p.id is not None]
    rows.append([InlineKeyboardButton(text="✅ Готово", callback_data="recipe:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def recipe_again_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ Добавить ещё", callback_data="recipe:add")], [InlineKeyboardButton(text="❌ Отмена", callback_data="recipe:cancel")]])
