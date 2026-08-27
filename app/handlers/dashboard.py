from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.dashboard import DashboardService
from app.services.user import UserService

router = Router(name="dashboard")
dashboard_service = DashboardService()
user_service = UserService()


@router.message(Command("dashboard", "stats"))
async def dashboard_handler(message: Message) -> None:
    if message.from_user is None:
        return
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None or user.id is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    await message.answer(await dashboard_service.build(user.id), parse_mode="HTML")


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "<b>MetaTrain</b>\n\n"
        "/start — профиль\n"
        "/profile — профиль и настройки\n"
        "/food — добавить еду\n"
        "/today — питание за сегодня\n"
        "/weight — записать вес\n"
        "/weights — история веса\n"
        "/workout — записать тренировку\n"
        "/workouts — история тренировок\n"
        "/dashboard — сводка\n"
        "/cancel — отменить текущий ввод",
        parse_mode="HTML",
    )
