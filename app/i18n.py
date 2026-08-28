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
    "menu_profile": {"ru": "👤 Профиль", "en": "👤 Profile"},
    "dashboard": {"ru": "🏠 Дашборд", "en": "🏠 Dashboard"},
    "refresh": {"ru": "🔄 Обновить", "en": "🔄 Refresh"},
    "back": {"ru": "⬅️ Назад", "en": "⬅️ Back"},
    "profile": {"ru": "👤 Профиль", "en": "👤 Profile"},
    "edit_profile": {"ru": "✏️ Изменить профиль", "en": "✏️ Edit profile"},
    "what_to_change": {"ru": "Что хочешь изменить?", "en": "What would you like to change?"},
    "gender": {"ru": "⚧ Пол", "en": "⚧ Gender"},
    "age": {"ru": "🎂 Возраст", "en": "🎂 Age"},
    "height": {"ru": "📏 Рост", "en": "📏 Height"},
    "weight": {"ru": "⚖️ Вес", "en": "⚖️ Weight"},
    "activity": {"ru": "🏃 Активность", "en": "🏃 Activity"},
    "goal": {"ru": "🎯 Цель", "en": "🎯 Goal"},
    "male": {"ru": "👨 Мужчина", "en": "👨 Male"},
    "female": {"ru": "👩 Женщина", "en": "👩 Female"},
    "sedentary": {"ru": "🪑 Минимальная", "en": "🪑 Sedentary"},
    "light": {"ru": "🚶 Лёгкая", "en": "🚶 Light"},
    "moderate": {"ru": "🏃 Средняя", "en": "🏃 Moderate"},
    "high": {"ru": "🏋️ Высокая", "en": "🏋️ High"},
    "very_high": {"ru": "🔥 Очень высокая", "en": "🔥 Very high"},
    "lose": {"ru": "🔥 Похудеть", "en": "🔥 Lose weight"},
    "maintain": {"ru": "⚖️ Поддерживать вес", "en": "⚖️ Maintain weight"},
    "gain": {"ru": "💪 Набрать массу", "en": "💪 Gain muscle"},
    "profile_updated": {"ru": "Профиль обновлён ✅", "en": "Profile updated ✅"},
    "profile_not_found": {"ru": "Профиль не найден", "en": "Profile not found"},
    "profile_not_filled": {"ru": "Профиль ещё не заполнен. Используй /start.", "en": "Your profile is not set up yet. Use /start."},
    "invalid_choice": {"ru": "Некорректный выбор", "en": "Invalid choice"},
    "enter_age": {"ru": "Введи новый возраст (14–100 лет).", "en": "Enter your new age (14–100)."},
    "enter_age_error": {"ru": "Введи возраст целым числом, например: 28", "en": "Enter your age as a whole number, e.g. 28"},
    "age_range": {"ru": "Возраст должен быть от 14 до 100 лет.", "en": "Age must be between 14 and 100."},
    "enter_height": {"ru": "Введи новый рост в сантиметрах (120–230).", "en": "Enter your new height in centimeters (120–230)."},
    "enter_height_error": {"ru": "Введи рост числом, например: 180", "en": "Enter your height as a number, e.g. 180"},
    "height_range": {"ru": "Рост должен быть от 120 до 230 см.", "en": "Height must be between 120 and 230 cm."},
    "enter_weight": {"ru": "Введи новый вес в килограммах (30–300).", "en": "Enter your new weight in kilograms (30–300)."},
    "enter_weight_error": {"ru": "Введи вес числом, например: 80", "en": "Enter your weight as a number, e.g. 80"},
    "weight_range": {"ru": "Вес должен быть от 30 до 300 кг.", "en": "Weight must be between 30 and 300 kg."},
    "choose_gender": {"ru": "Выбери пол:", "en": "Choose your gender:"},
    "choose_activity": {"ru": "Выбери уровень активности:", "en": "Choose your activity level:"},
    "choose_goal": {"ru": "Какая у тебя цель?", "en": "What is your goal?"},
    "welcome": {
        "ru": "<b>Добро пожаловать в MetaTrain! 👋</b>\n\nТвой личный помощник для питания, тренировок и прогресса.\n\nВ одном месте ты сможешь:\n🥗 вести питание и смотреть дневную норму\n🏋️ записывать тренировки и отслеживать результаты\n⚖️ контролировать вес\n📈 видеть свой прогресс и историю\n\nНикаких сложных команд — после настройки профиля всё будет доступно с главного экрана.\n\n<b>Давай начнём с нескольких вопросов о тебе.</b>",
        "en": "<b>Welcome to MetaTrain! 👋</b>\n\nYour personal assistant for nutrition, workouts, and progress.\n\nIn one place you can:\n🥗 track food and your daily targets\n🏋️ log workouts and track results\n⚖️ track your weight\n📈 see your progress and history\n\nNo complicated commands — after setup, everything is available from the main screen.\n\n<b>Let's start with a few questions about you.</b>",
    },
}


def t(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    values = TEXTS[key]
    return values.get(lang, values[DEFAULT_LANGUAGE])
