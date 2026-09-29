from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def product_keyboard(products, recipes=None, lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for p in products: rows.append([InlineKeyboardButton(text=f"🥗 {p.name[:35]}", callback_data=f"food:product:{p.id}")])
    for r in recipes or []: rows.append([InlineKeyboardButton(text=f"🍲 {r.name[:35]}", callback_data=f"food:recipe:{r.id}")])
    rows.append([InlineKeyboardButton(text=t("new_product", lang), callback_data="food:product:new")])
    rows.append([InlineKeyboardButton(text=t("back", lang), callback_data="dashboard:food")])
    rows.append([InlineKeyboardButton(text=t("dashboard", lang), callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def catalog_start_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("find_product", lang), callback_data="food:catalog:search")],
        [InlineKeyboardButton(text=t("meal_back", lang), callback_data="dashboard:food")],
        [InlineKeyboardButton(text=t("dashboard", lang), callback_data="dashboard:home")],
    ])


def catalog_keyboard(items, lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        details = []
        if item.preparation: details.append(item.preparation)
        if item.brand: details.append(item.brand)
        suffix = f" · {' · '.join(details)}" if details else ""
        available = max(1, 42 - len(suffix)); label = f"🍽 {item.name[:available]}{suffix}"
        rows.append([InlineKeyboardButton(text=label[:64], callback_data=f"food:catalog:{item.id}")])
    rows.append([InlineKeyboardButton(text=t("new_search", lang), callback_data="food:catalog:search")])
    rows.append([InlineKeyboardButton(text=t("meal_back", lang), callback_data="dashboard:food")])
    rows.append([InlineKeyboardButton(text=t("dashboard", lang), callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
