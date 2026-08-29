from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def exercise_categories(lang: str = "en") -> InlineKeyboardMarkup:
    labels = {
        "chest": ("💪 Грудь", "💪 Chest"), "back": ("🪽 Спина", "🪽 Back"),
        "legs": ("🦵 Ноги", "🦵 Legs"), "shoulders": ("🏋️ Плечи", "🏋️ Shoulders"),
        "arms": ("💪 Руки", "💪 Arms"), "core": ("🔥 Пресс", "🔥 Core"),
    }
    rows = []
    keys = list(labels)
    for i in range(0, len(keys), 2):
        rows.append([InlineKeyboardButton(text=labels[k][0 if lang == "ru" else 1], callback_data=f"workout:category:{k}") for k in keys[i:i + 2]])
    rows.append([InlineKeyboardButton(text="🔎 Поиск" if lang == "ru" else "🔎 Search", callback_data="workout:search")])
    rows.append([InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def exercise_list(items, lang: str = "en", category: str | None = None) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        name = item.name_ru if lang == "ru" else item.name_en
        equipment = item.equipment_ru if lang == "ru" else item.equipment_en
        rows.append([InlineKeyboardButton(text=f"{name} · {equipment}"[:64], callback_data=f"workout:exercise:{item.id}")])
    rows.append([InlineKeyboardButton(text="◀️ Группы" if lang == "ru" else "◀️ Muscle groups", callback_data="workout:menu")])
    rows.append([InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def exercise_search_result(items, lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        name = item.name_ru if lang == "ru" else item.name_en
        rows.append([InlineKeyboardButton(text=name[:64], callback_data=f"workout:exercise:{item.id}")])
    rows.append([InlineKeyboardButton(text="🔎 Новый поиск" if lang == "ru" else "🔎 New search", callback_data="workout:search")])
    rows.append([InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def current_workout_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить упражнение" if lang == "ru" else "➕ Add exercise", callback_data="workout:add")],
        [InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")],
        [InlineKeyboardButton(text="✅ Завершить" if lang == "ru" else "✅ Finish workout", callback_data="workout:finish")],
    ])


def workout_set_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Следующий подход" if lang == "ru" else "➕ Next set", callback_data="workout:set:next")],
        [InlineKeyboardButton(text="📋 Текущая тренировка" if lang == "ru" else "📋 Current workout", callback_data="workout:current")],
        [InlineKeyboardButton(text="🔄 Другое упражнение" if lang == "ru" else "🔄 Another exercise", callback_data="workout:add")],
        [InlineKeyboardButton(text="✅ Завершить" if lang == "ru" else "✅ Finish workout", callback_data="workout:finish"), InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")],
    ])


def previous_set_keyboard(weight: float, reps: int, lang: str = "en") -> InlineKeyboardMarkup:
    reuse = f"↩️ Повторить {weight:g} кг × {reps}" if lang == "ru" else f"↩️ Repeat {weight:g} kg × {reps}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=reuse, callback_data="workout:set:repeat")],
        [InlineKeyboardButton(text="✏️ Ввести вручную" if lang == "ru" else "✏️ Enter manually", callback_data="workout:set:manual")],
        [InlineKeyboardButton(text="📋 Текущая тренировка" if lang == "ru" else "📋 Current workout", callback_data="workout:current")],
        [InlineKeyboardButton(text="🔄 Другое упражнение" if lang == "ru" else "🔄 Another exercise", callback_data="workout:add")],
        [InlineKeyboardButton(text="✅ Завершить" if lang == "ru" else "✅ Finish workout", callback_data="workout:finish"), InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")],
    ])
