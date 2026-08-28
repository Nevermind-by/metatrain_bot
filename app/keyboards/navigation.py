from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def navigation_keyboard(
    *,
    lang: str = "en",
    back_callback: str = "dashboard:home",
    back_text: str | None = None,
    include_dashboard: bool = True,
) -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(text=back_text or t("back", lang), callback_data=back_callback)]
    if include_dashboard:
        row.append(InlineKeyboardButton(text=t("dashboard", lang), callback_data="dashboard:home"))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def dashboard_only_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return navigation_keyboard(lang=lang, include_dashboard=False, back_text=t("dashboard", lang))
