from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import ProfileStates
from app.handlers.dashboard import _render
from app.keyboards.profile import activity_keyboard, gender_keyboard, goal_keyboard
from app.services.profile import ProfileService
from app.services.user import UserService

router = Router(name="start")
user_service = UserService()
profile_service = ProfileService()


WELCOME_TEXT = (
    "<b>Добро пожаловать в MetaTrain! 👋</b>\n\n"
    "Твой личный помощник для питания, тренировок и прогресса.\n\n"
    "В одном месте ты сможешь:\n"
    "🥗 вести питание и смотреть дневную норму\n"
    "🏋️ записывать тренировки и отслеживать результаты\n"
    "⚖️ контролировать вес\n"
    "📈 видеть свой прогресс и историю\n\n"
    "Никаких сложных команд — после настройки профиля всё будет доступно с главного экрана.\n\n"
    "<b>Давай начнём с нескольких вопросов о тебе.</b>"
)


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    user, _ = await user_service.register(message.from_user)
    if user.id is not None:
        existing_profile = await profile_service.get_profile(user.id)
        if existing_profile is not None:
            await state.clear()
            await _render(message, user.id)
            return

    await state.clear()
    await state.update_data(user_id=user.id)
    await message.answer(WELCOME_TEXT)
    await message.answer(
        "<b>Настроим твой профиль</b> 👤\n\n"
        "Это нужно, чтобы рассчитать твою персональную дневную норму и точнее подбирать рекомендации.\n\n"
        "Начнём с пола:",
        reply_markup=gender_keyboard(),
    )
    await state.set_state(ProfileStates.gender)


@router.callback_query(ProfileStates.gender, F.data.startswith("profile:gender:"))
async def gender_handler(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.rsplit(":", 1)[-1]
    if gender not in {"male", "female"}:
        await callback.answer("Некорректный выбор", show_alert=True)
        return
    await state.update_data(gender=gender)
    await state.set_state(ProfileStates.age)
    if callback.message is not None:
        await callback.message.edit_text("Сколько тебе лет? Введи возраст числом.")
    await callback.answer()


@router.message(ProfileStates.age)
async def age_handler(message: Message, state: FSMContext) -> None:
    try:
        age = int(message.text or "")
    except ValueError:
        await message.answer("Введи возраст целым числом, например: 28")
        return
    if not 14 <= age <= 100:
        await message.answer("Возраст должен быть от 14 до 100 лет.")
        return
    await state.update_data(age=age)
    await state.set_state(ProfileStates.height)
    await message.answer("Какой у тебя рост? Введи в сантиметрах, например: 180")


@router.message(ProfileStates.height)
async def height_handler(message: Message, state: FSMContext) -> None:
    try:
        height = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи рост числом, например: 180")
        return
    if not 120 <= height <= 230:
        await message.answer("Рост должен быть от 120 до 230 см.")
        return
    await state.update_data(height_cm=height)
    await state.set_state(ProfileStates.weight)
    await message.answer("Какой у тебя вес? Введи в килограммах, например: 80")


@router.message(ProfileStates.weight)
async def weight_handler(message: Message, state: FSMContext) -> None:
    try:
        weight = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи вес числом, например: 80")
        return
    if not 30 <= weight <= 300:
        await message.answer("Вес должен быть от 30 до 300 кг.")
        return
    await state.update_data(weight_kg=weight)
    await state.set_state(ProfileStates.activity_level)
    await message.answer("Насколько ты активен в течение недели?", reply_markup=activity_keyboard())


@router.callback_query(ProfileStates.activity_level, F.data.startswith("profile:activity:"))
async def activity_handler(callback: CallbackQuery, state: FSMContext) -> None:
    activity_level = callback.data.rsplit(":", 1)[-1]
    if activity_level not in {"sedentary", "light", "moderate", "high", "very_high"}:
        await callback.answer("Некорректный выбор", show_alert=True)
        return
    await state.update_data(activity_level=activity_level)
    await state.set_state(ProfileStates.goal)
    if callback.message is not None:
        await callback.message.edit_text("Какая у тебя цель?", reply_markup=goal_keyboard())
    await callback.answer()


@router.callback_query(ProfileStates.goal, F.data.startswith("profile:goal:"))
async def goal_handler(callback: CallbackQuery, state: FSMContext) -> None:
    goal = callback.data.rsplit(":", 1)[-1]
    if goal not in {"lose", "maintain", "gain"}:
        await callback.answer("Некорректный выбор", show_alert=True)
        return

    data = await state.get_data()
    user_id = data.get("user_id")
    if user_id is None:
        await callback.answer("Не удалось найти пользователя", show_alert=True)
        return

    await profile_service.create_profile(
        user_id=user_id,
        gender=data["gender"],
        age=data["age"],
        height_cm=data["height_cm"],
        weight_kg=data["weight_kg"],
        activity_level=data["activity_level"],
        goal=goal,
    )
    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text("<b>Профиль готов! 🎉</b>")
        await _render(callback, user_id)
    await callback.answer()
