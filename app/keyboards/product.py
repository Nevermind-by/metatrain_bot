from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def product_keyboard(products) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=p.name[:40], callback_data=f"food:product:{p.id}")] for p in products]
    rows.append([InlineKeyboardButton(text="➕ Новый продукт", callback_data="food:product:new")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
