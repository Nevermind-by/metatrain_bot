from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.services.user import UserService


router = Router(name="start")
user_service = UserService()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    if message.from_user is None:
        return

    user, created = await user_service.register(message.from_user)

    if created:
        text = (
            f"Привет, {user.first_name or 'друг'}! 👋\n\n"
            "Добро пожаловать в MetaTrain."
        )
    else:
        text = f"С возвращением, {user.first_name or 'друг'}! 👋"

    await message.answer(text)
