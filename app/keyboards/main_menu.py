from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


MAIN_MENU_TEXTS = {
    "food": "🍽 Питание",
    "workout": "🏋️ Тренировка",
    "weight": "⚖️ Вес",
    "progress": "📈 Прогресс",
    "dashboard": "📊 Сводка",
    "profile": "👤 Профиль",
}


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MAIN_MENU_TEXTS["food"]), KeyboardButton(text=MAIN_MENU_TEXTS["workout"])],
            [KeyboardButton(text=MAIN_MENU_TEXTS["weight"]), KeyboardButton(text=MAIN_MENU_TEXTS["progress"])],
            [KeyboardButton(text=MAIN_MENU_TEXTS["dashboard"]), KeyboardButton(text=MAIN_MENU_TEXTS["profile"])],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери действие…",
    )
