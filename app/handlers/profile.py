from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards.profile import profile_keyboard
from app.services.profile import ProfileService

router = Router(name="profile")
profile_service = ProfileService()


@router.message(Command("profile"))
async def profile_handler(message: Message) -> None:
    if message.from_user is None:
        return

    profile = await profile_service.get_profile(message.from_user.id)
    if profile is None:
        await message.answer("Профиль ещё не заполнен. Используй /start.")
        return

    await message.answer(
        profile_service.format_profile(profile),
        reply_markup=profile_keyboard(),
    )


@router.callback_query(F.data == "profile:show")
async def profile_callback(callback: CallbackQuery) -> None:
    profile = await profile_service.get_profile(callback.from_user.id)
    if profile is None:
        await callback.answer("Профиль не заполнен", show_alert=True)
        return

    if callback.message is not None:
        await callback.message.edit_text(
            profile_service.format_profile(profile),
            reply_markup=profile_keyboard(),
        )
    await callback.answer()
