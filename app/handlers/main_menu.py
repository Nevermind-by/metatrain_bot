from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states import FoodStates, ProgressStates, WeightStates, WorkoutStates
from app.handlers.dashboard import _render
from app.keyboards.main_menu import MAIN_MENU_TEXTS
from app.keyboards.profile_view import profile_keyboard
from app.services.profile import ProfileService
from app.services.user import UserService

router = Router(name="main_menu")
user_service = UserService()
profile_service = ProfileService()


async def _user_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    user = await user_service.get_by_telegram_id(message.from_user.id)
    return user.id if user is not None else None


@router.message(F.text == MAIN_MENU_TEXTS["food"])
async def food_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(FoodStates.meal)
    await message.answer("Выбери приём пищи: завтрак, обед, ужин или перекус.")


@router.message(F.text == MAIN_MENU_TEXTS["workout"])
async def workout_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(WorkoutStates.name)
    await message.answer("Название тренировки? Например: Грудь + трицепс")


@router.message(F.text == MAIN_MENU_TEXTS["weight"])
async def weight_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(WeightStates.value)
    await message.answer("Введи текущий вес в кг, например: 82.4")


@router.message(F.text == MAIN_MENU_TEXTS["progress"])
async def progress_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProgressStates.exercise)
    await message.answer("Какое упражнение показать? Например: Жим лёжа")


@router.message(F.text == MAIN_MENU_TEXTS["dashboard"])
async def dashboard_menu(message: Message) -> None:
    user_id = await _user_id(message)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    await _render(message, user_id)


@router.message(F.text == MAIN_MENU_TEXTS["profile"])
async def profile_menu(message: Message) -> None:
    user_id = await _user_id(message)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    profile = await profile_service.get_profile(user_id)
    if profile is None:
        await message.answer("Профиль ещё не заполнен. Используй /start.")
        return
    await message.answer(profile_service.format_profile(profile), parse_mode="HTML", reply_markup=profile_keyboard())
