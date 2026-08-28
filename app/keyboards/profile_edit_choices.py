from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def gender_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Мужчина", callback_data="profile:gender:male"), InlineKeyboardButton(text="👩 Женщина", callback_data="profile:gender:female")],
        [InlineKeyboardButton(text="◀️ Профиль", callback_data="profile:show"), InlineKeyboardButton(text="🏠 Дашборд", callback_data="dashboard:home")],
    ])


def activity_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪑 Минимальная", callback_data="profile:activity:sedentary")],
        [InlineKeyboardButton(text="🚶 Лёгкая", callback_data="profile:activity:light")],
        [InlineKeyboardButton(text="🏃 Средняя", callback_data="profile:activity:moderate")],
        [InlineKeyboardButton(text="🏋️ Высокая", callback_data="profile:activity:high")],
        [InlineKeyboardButton(text="🔥 Очень высокая", callback_data="profile:activity:very_high")],
        [InlineKeyboardButton(text="◀️ Профиль", callback_data="profile:show"), InlineKeyboardButton(text="🏠 Дашборд", callback_data="dashboard:home")],
    ])


def goal_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Похудеть", callback_data="profile:goal:lose")],
        [InlineKeyboardButton(text="⚖️ Поддерживать вес", callback_data="profile:goal:maintain")],
        [InlineKeyboardButton(text="💪 Набрать массу", callback_data="profile:goal:gain")],
        [InlineKeyboardButton(text="◀️ Профиль", callback_data="profile:show"), InlineKeyboardButton(text="🏠 Дашборд", callback_data="dashboard:home")],
    ])
