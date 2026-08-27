from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def activity_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🪑 Минимальная", callback_data="profile:activity:sedentary")],
            [InlineKeyboardButton(text="🚶 Лёгкая", callback_data="profile:activity:light")],
            [InlineKeyboardButton(text="🏃 Средняя", callback_data="profile:activity:moderate")],
            [InlineKeyboardButton(text="🏋️ Высокая", callback_data="profile:activity:high")],
            [InlineKeyboardButton(text="🔥 Очень высокая", callback_data="profile:activity:very_high")],
        ]
    )
