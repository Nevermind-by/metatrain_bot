from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def product_keyboard(products, recipes=None) -> InlineKeyboardMarkup:
    rows = []
    for p in products:
        rows.append([InlineKeyboardButton(text=f"🥗 {p.name[:35]}", callback_data=f"food:product:{p.id}")])
    for r in recipes or []:
        rows.append([InlineKeyboardButton(text=f"🍲 {r.name[:35]}", callback_data=f"food:recipe:{r.id}")])
    rows.append([InlineKeyboardButton(text="➕ Новый продукт", callback_data="food:product:new")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
