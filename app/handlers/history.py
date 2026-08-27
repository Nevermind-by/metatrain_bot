from collections import defaultdict
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.food import FoodService
from app.services.user import UserService

router = Router(name="history")
food_service = FoodService()
user_service = UserService()


@router.message(Command("history"))
async def history_handler(message: Message) -> None:
    if message.from_user is None:
        return
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None or user.id is None:
        await message.answer("Сначала создай профиль через /start.")
        return

    entries = await food_service.history(user.id, 7)
    if not entries:
        await message.answer("За последние 7 дней записей питания нет.")
        return

    daily = defaultdict(list)
    for entry in entries:
        daily[entry.eaten_at.date().isoformat()].append(entry)

    lines = ["📈 <b>Питание за 7 дней</b>", ""]
    for day in sorted(daily, reverse=True):
        total = food_service.totals(daily[day])
        label = datetime.fromisoformat(day).strftime("%d.%m")
        lines.append(f"<b>{label}</b> — {total['calories']:g} ккал • Б {total['protein']:g} • Ж {total['fat']:g} • У {total['carbohydrates']:g}")
    lines.extend([
        "",
        f"Среднее: {food_service.average_daily_calories(entries, 7):g} ккал/день",
    ])
    await message.answer("\n".join(lines), parse_mode="HTML")
