from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def edit_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚧ Пол", callback_data="profile:edit:gender")],
            [InlineKeyboardButton(text="🎂 Возраст", callback_data="profile:edit:age")],
            [InlineKeyboardButton(text="📏 Рост", callback_data="profile:edit:height")],
            [InlineKeyboardButton(text="⚖️ Вес", callback_data="profile:edit:weight")],
            [InlineKeyboardButton(text="🏃 Активность", callback_data="profile:edit:activity")],
            [InlineKeyboardButton(text="🎯 Цель", callback_data="profile:edit:goal")],
            [InlineKeyboardButton(text="◀️ Профиль", callback_data="profile:show")],
            [InlineKeyboardButton(text="🏠 Дашборд", callback_data="dashboard:home")],
        ]
    )
