from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def navigation_keyboard(
    *,
    back_callback: str = "dashboard:home",
    back_text: str = "⬅️ Назад",
    include_dashboard: bool = True,
) -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(text=back_text, callback_data=back_callback)]
    if include_dashboard:
        row.append(InlineKeyboardButton(text="🏠 Дашборд", callback_data="dashboard:home"))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def dashboard_only_keyboard() -> InlineKeyboardMarkup:
    return navigation_keyboard(include_dashboard=False, back_text="🏠 Дашборд")
