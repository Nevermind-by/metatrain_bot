from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states import FoodStates, ProgressStates, WeightStates, WorkoutStates
from app.handlers.dashboard import _render
from app.handlers.workout import open_workout_menu
from app.i18n import language_code
from app.keyboards.food_flow import meal_keyboard
from app.keyboards.main_menu import main_menu_texts
from app.keyboards.navigation import navigation_keyboard
from app.keyboards.profile_view import profile_keyboard
from app.services.profile import ProfileService
from app.services.user import UserService

router = Router(name="main_menu")
user_service = UserService()
profile_service = ProfileService()


def _matches_menu(key: str):
    return F.text.in_({main_menu_texts("ru")[key], main_menu_texts("en")[key]})


async def _user_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    user = await user_service.get_by_telegram_id(message.from_user.id)
    return user.id if user is not None else None


@router.message(_matches_menu("food"))
async def food_menu(message: Message, state: FSMContext) -> None:
    await state.clear(); await state.set_state(FoodStates.meal)
    lang = language_code(message.from_user)
    text = "🍽 <b>Добавить питание</b>\n\nВыбери приём пищи:" if lang == "ru" else "🍽 <b>Add nutrition</b>\n\nChoose a meal:"
    await message.answer(text, parse_mode="HTML", reply_markup=meal_keyboard(lang))


@router.message(_matches_menu("workout"))
async def workout_menu(message: Message, state: FSMContext) -> None:
    await open_workout_menu(message, state)


@router.message(_matches_menu("weight"))
async def weight_menu(message: Message, state: FSMContext) -> None:
    await state.clear(); await state.set_state(WeightStates.value)
    lang = language_code(message.from_user)
    text = "⚖️ <b>Записать вес</b>\n\nВведи текущий вес в кг, например: 82.4" if lang == "ru" else "⚖️ <b>Log weight</b>\n\nEnter your current weight in kg, for example: 82.4"
    await message.answer(text, parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))


@router.message(_matches_menu("progress"))
async def progress_menu(message: Message, state: FSMContext) -> None:
    await state.clear(); await state.set_state(ProgressStates.exercise)
    lang = language_code(message.from_user)
    text = "📈 <b>Прогресс упражнения</b>\n\nКакое упражнение показать? Например: Жим лёжа" if lang == "ru" else "📈 <b>Exercise progress</b>\n\nWhich exercise should I show? For example: Bench press"
    await message.answer(text, parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))


@router.message(_matches_menu("dashboard"))
async def dashboard_menu(message: Message) -> None:
    user_id = await _user_id(message)
    lang = language_code(message.from_user)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start first.")
        return
    await _render(message, user_id)


@router.message(_matches_menu("profile"))
async def profile_menu(message: Message) -> None:
    user_id = await _user_id(message)
    lang = language_code(message.from_user)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start first.")
        return
    profile = await profile_service.get_profile(user_id)
    if profile is None:
        await message.answer("Профиль ещё не заполнен. Используй /start." if lang == "ru" else "Your profile is not set up yet. Use /start.")
        return
    await message.answer(profile_service.format_profile(profile, lang=lang), parse_mode="HTML", reply_markup=profile_keyboard(lang))
