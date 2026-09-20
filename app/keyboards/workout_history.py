from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def workout_history_keyboard(items, lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        label = item.performed_at.strftime("%d.%m %H:%M")
        name = item.name.replace("\n", " ")[:36]
        rows.append([
            InlineKeyboardButton(
                text=f"📋 {name} · {label}",
                callback_data=f"dashboard:workout:history:{item.id}",
            )
        ])
    rows.append([InlineKeyboardButton(text="🏠 Дашборд" if lang == "ru" else "🏠 Dashboard", callback_data="dashboard:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
