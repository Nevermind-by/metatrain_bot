from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Мужчина", callback_data="profile:gender:male"),
                InlineKeyboardButton(text="👩 Женщина", callback_data="profile:gender:female"),
            ]
        ]
    )


def goal_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Похудеть", callback_data="profile:goal:lose")],
            [InlineKeyboardButton(text="⚖️ Поддерживать вес", callback_data="profile:goal:maintain")],
            [InlineKeyboardButton(text="💪 Набрать массу", callback_data="profile:goal:gain")],
        ]
    )


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить профиль", callback_data="profile:edit")]
        ]
    )
