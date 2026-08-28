from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def gender_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    labels = {"ru": ("👨 Мужчина", "👩 Женщина"), "en": ("👨 Male", "👩 Female")}
    male, female = labels.get(lang, labels["en"])
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=male, callback_data="profile:gender:male"),
        InlineKeyboardButton(text=female, callback_data="profile:gender:female"),
    ]])


def activity_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    labels = {
        "ru": [("🪑 Минимальная", "sedentary"), ("🚶 Лёгкая", "light"), ("🏃 Средняя", "moderate"), ("🏋️ Высокая", "high"), ("🔥 Очень высокая", "very_high")],
        "en": [("🪑 Sedentary", "sedentary"), ("🚶 Light", "light"), ("🏃 Moderate", "moderate"), ("🏋️ High", "high"), ("🔥 Very high", "very_high")],
    }
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"profile:activity:{value}")] for text, value in labels.get(lang, labels["en"])
    ])


def goal_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    labels = {
        "ru": [("🔥 Похудеть", "lose"), ("⚖️ Поддерживать вес", "maintain"), ("💪 Набрать массу", "gain")],
        "en": [("🔥 Lose weight", "lose"), ("⚖️ Maintain weight", "maintain"), ("💪 Gain muscle", "gain")],
    }
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"profile:goal:{value}")] for text, value in labels.get(lang, labels["en"])
    ])
