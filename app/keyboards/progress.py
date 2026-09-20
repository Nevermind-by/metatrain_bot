from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


_GROUPS = (
    ("chest", ("💪 Грудь", "💪 Chest")),
    ("back", ("🪽 Спина", "🪽 Back")),
    ("legs", ("🦵 Ноги", "🦵 Legs")),
    ("shoulders", ("🏋️ Плечи", "🏋️ Shoulders")),
    ("arms", ("💪 Руки", "💪 Arms")),
    ("core", ("🔥 Пресс", "🔥 Core")),
)


def progress_categories(lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(_GROUPS), 2):
        rows.append([
            InlineKeyboardButton(text=label[0 if lang == "ru" else 1], callback_data=f"progress:category:{code}")
            for code, label in _GROUPS[i:i + 2]
        ])
    rows.append([InlineKeyboardButton(text="🔎 Поиск" if lang == "ru" else "🔎 Search", callback_data="progress:search")])
    rows.append([InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def progress_exercise_list(items, lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        name = item.name_ru if lang == "ru" else item.name_en
        equipment = item.equipment_ru if lang == "ru" else item.equipment_en
        rows.append([InlineKeyboardButton(text=f"{name} · {equipment}"[:64], callback_data=f"progress:exercise:{item.id}")])
    rows.append([InlineKeyboardButton(text="◀️ Группы" if lang == "ru" else "◀️ Muscle groups", callback_data="progress:menu")])
    rows.append([InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def progress_search_results(items, lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        name = item.name_ru if lang == "ru" else item.name_en
        rows.append([InlineKeyboardButton(text=name[:64], callback_data=f"progress:exercise:{item.id}")])
    rows.append([InlineKeyboardButton(text="🔎 Новый поиск" if lang == "ru" else "🔎 New search", callback_data="progress:search")])
    rows.append([InlineKeyboardButton(text="◀️ Группы" if lang == "ru" else "◀️ Muscle groups", callback_data="progress:menu")])
    rows.append([InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
