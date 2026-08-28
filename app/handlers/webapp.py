from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from aiogram import Router

from app.config.settings import settings

router = Router(name="webapp")


@router.message(Command("webapp"))
async def webapp_handler(message: Message) -> None:
    if not settings.web_app_url:
        await message.answer(
            "Web App ещё не настроен. Укажи WEB_APP_URL в .env — нужен публичный HTTPS-адрес."
        )
        return
    await message.answer(
        "Открой MetaTrain в приложении 👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🌐 Открыть MetaTrain",
                        web_app=WebAppInfo(url=settings.web_app_url),
                    )
                ]
            ]
        ),
    )
