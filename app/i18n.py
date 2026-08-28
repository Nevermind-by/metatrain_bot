from __future__ import annotations

from aiogram.types import User as TelegramUser

SUPPORTED_LANGUAGES = {"ru", "en"}
DEFAULT_LANGUAGE = "en"


def language_code(user: TelegramUser | None) -> str:
    """Return the UI language from Telegram, defaulting to English."""
    if user is None:
        return DEFAULT_LANGUAGE
    code = (user.language_code or "").lower().split("-")[0]
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


TEXTS = {
    "menu_food": {"ru": "🍽 Питание", "en": "🍽 Nutrition"},
    "menu_workout": {"ru": "🏋️ Тренировка", "en": "🏋️ Workout"},
    "menu_weight": {"ru": "⚖️ Вес", "en": "⚖️ Weight"},
    "menu_progress": {"ru": "📈 Прогресс", "en": "📈 Progress"},
    "menu_dashboard": {"ru": "📊 Сводка", "en": "📊 Dashboard"},
    "menu_profile": {"ru": "👤 Профиль", "en": "👤 Profile"},
    "menu_placeholder": {"ru": "Выбери действие…", "en": "Choose an action…"},
    "find_product": {"ru": "🔎 Найти продукт", "en": "🔎 Find a food"},
    "new_search": {"ru": "🔎 Новый поиск", "en": "🔎 New search"},
    "new_product": {"ru": "➕ Новый продукт", "en": "➕ New product"},
    "meal_back": {"ru": "⬅️ Приём пищи", "en": "⬅️ Meal"},
    "dashboard": {"ru": "🏠 Дашборд", "en": "🏠 Dashboard"},
    "refresh": {"ru": "🔄 Обновить", "en": "🔄 Refresh"},
    "back": {"ru": "⬅️ Назад", "en": "⬅️ Back"},
    "welcome": {
        "ru": "<b>Добро пожаловать в MetaTrain! 👋</b>\n\nТвой личный помощник для питания, тренировок и прогресса.\n\nВ одном месте ты сможешь:\n🥗 вести питание и смотреть дневную норму\n🏋️ записывать тренировки и отслеживать результаты\n⚖️ контролировать вес\n📈 видеть свой прогресс и историю\n\nНикаких сложных команд — после настройки профиля всё будет доступно с главного экрана.\n\n<b>Давай начнём с нескольких вопросов о тебе.</b>",
        "en": "<b>Welcome to MetaTrain! 👋</b>\n\nYour personal assistant for nutrition, workouts, and progress.\n\nIn one place you can:\n🥗 track food and your daily targets\n🏋️ log workouts and track results\n⚖️ track your weight\n📈 see your progress and history\n\nNo complicated commands — after setup, everything is available from the main screen.\n\n<b>Let's start with a few questions about you.</b>",
    },
}


def t(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    values = TEXTS[key]
    return values.get(lang, values[DEFAULT_LANGUAGE])
