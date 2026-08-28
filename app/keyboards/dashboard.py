from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽 Добавить еду", callback_data="dashboard:food")],
        [InlineKeyboardButton(text="📅 Питание сегодня", callback_data="dashboard:today")],
        [InlineKeyboardButton(text="📚 История питания", callback_data="dashboard:history")],
        [InlineKeyboardButton(text="🏋️ Тренировка", callback_data="dashboard:workout")],
        [InlineKeyboardButton(text="🏋️ История тренировок", callback_data="dashboard:workouts")],
        [InlineKeyboardButton(text="⚖️ Записать вес", callback_data="dashboard:weight")],
        [InlineKeyboardButton(text="📈 Прогресс", callback_data="dashboard:progress")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="dashboard:profile")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="dashboard:refresh")],
    ])
