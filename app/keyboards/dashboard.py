from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍽 Питание", callback_data="dashboard:food"),
                InlineKeyboardButton(text="🏋️ Тренировка", callback_data="dashboard:workout"),
            ],
            [
                InlineKeyboardButton(text="⚖️ Вес", callback_data="dashboard:weight"),
                InlineKeyboardButton(text="📈 Прогресс", callback_data="dashboard:progress"),
            ],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="dashboard:profile")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="dashboard:refresh")],
        ]
    )
