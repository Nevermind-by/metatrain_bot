from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import ProfileStates
from app.handlers.dashboard import _render
from app.i18n import language_code
from app.keyboards.profile import activity_keyboard, gender_keyboard, goal_keyboard
from app.services.profile import ProfileService
from app.services.user import UserService

router = Router(name="start")
user_service = UserService()
profile_service = ProfileService()

WELCOME = {
    "ru": "<b>Добро пожаловать в MetaTrain! 👋</b>\n\nТвой личный помощник для питания, тренировок и прогресса.\n\nВ одном месте ты сможешь:\n🥗 вести питание и смотреть дневную норму\n🏋️ записывать тренировки и отслеживать результаты\n⚖️ контролировать вес\n📈 видеть свой прогресс и историю\n\nНикаких сложных команд — после настройки профиля всё будет доступно с главного экрана.\n\n<b>Давай начнём с нескольких вопросов о тебе.</b>",
    "en": "<b>Welcome to MetaTrain! 👋</b>\n\nYour personal assistant for nutrition, workouts, and progress.\n\nIn one place you can:\n🥗 track food and daily targets\n🏋️ log workouts and track results\n⚖️ track your weight\n📈 see your progress and history\n\nNo complicated commands — after setup, everything is available from the main screen.\n\n<b>Let's start with a few questions about you.</b>",
}


def _lang(obj) -> str:
    return language_code(obj.from_user)


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lang = language_code(message.from_user)
    user, _ = await user_service.register(message.from_user)
    if user.id is not None:
        existing_profile = await profile_service.get_profile(user.id)
        if existing_profile is not None:
            await state.clear()
            await _render(message, user.id)
            return
    await state.clear()
    await state.update_data(user_id=user.id)
    await message.answer(WELCOME[lang], parse_mode="HTML")
    if lang == "ru":
        text = "<b>Настроим твой профиль</b> 👤\n\nЭто нужно, чтобы рассчитать твою персональную дневную норму и точнее подбирать рекомендации.\n\nНачнём с пола:"
    else:
        text = "<b>Let's set up your profile</b> 👤\n\nThis lets me calculate your personal daily target and provide better recommendations.\n\nLet's start with your gender:"
    await message.answer(text, parse_mode="HTML", reply_markup=gender_keyboard(lang))
    await state.set_state(ProfileStates.gender)


@router.callback_query(ProfileStates.gender, F.data.startswith("profile:gender:"))
async def gender_handler(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.rsplit(":", 1)[-1]
    if gender not in {"male", "female"}:
        await callback.answer("Некорректный выбор" if _lang(callback) == "ru" else "Invalid choice", show_alert=True)
        return
    lang = _lang(callback)
    await state.update_data(gender=gender)
    await state.set_state(ProfileStates.age)
    if callback.message is not None:
        await callback.message.edit_text("Сколько тебе лет? Введи возраст числом." if lang == "ru" else "How old are you? Enter your age as a number.")
    await callback.answer()


@router.message(ProfileStates.age)
async def age_handler(message: Message, state: FSMContext) -> None:
    lang = _lang(message)
    try: age = int(message.text or "")
    except ValueError:
        await message.answer("Введи возраст целым числом, например: 28" if lang == "ru" else "Enter your age as a whole number, e.g. 28"); return
    if not 14 <= age <= 100:
        await message.answer("Возраст должен быть от 14 до 100 лет." if lang == "ru" else "Age must be between 14 and 100."); return
    await state.update_data(age=age); await state.set_state(ProfileStates.height)
    await message.answer("Какой у тебя рост? Введи в сантиметрах, например: 180" if lang == "ru" else "What is your height? Enter it in centimeters, e.g. 180")


@router.message(ProfileStates.height)
async def height_handler(message: Message, state: FSMContext) -> None:
    lang = _lang(message)
    try: height = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи рост числом, например: 180" if lang == "ru" else "Enter your height as a number, e.g. 180"); return
    if not 120 <= height <= 230:
        await message.answer("Рост должен быть от 120 до 230 см." if lang == "ru" else "Height must be between 120 and 230 cm."); return
    await state.update_data(height_cm=height); await state.set_state(ProfileStates.weight)
    await message.answer("Какой у тебя вес? Введи в килограммах, например: 80" if lang == "ru" else "What is your weight? Enter it in kg, e.g. 80")


@router.message(ProfileStates.weight)
async def weight_handler(message: Message, state: FSMContext) -> None:
    lang = _lang(message)
    try: weight = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи вес числом, например: 80" if lang == "ru" else "Enter your weight as a number, e.g. 80"); return
    if not 30 <= weight <= 300:
        await message.answer("Вес должен быть от 30 до 300 кг." if lang == "ru" else "Weight must be between 30 and 300 kg."); return
    await state.update_data(weight_kg=weight); await state.set_state(ProfileStates.activity_level)
    await message.answer("Насколько ты активен в течение недели?" if lang == "ru" else "How active are you during the week?", reply_markup=activity_keyboard(lang))


@router.callback_query(ProfileStates.activity_level, F.data.startswith("profile:activity:"))
async def activity_handler(callback: CallbackQuery, state: FSMContext) -> None:
    activity_level = callback.data.rsplit(":", 1)[-1]
    lang = _lang(callback)
    if activity_level not in {"sedentary", "light", "moderate", "high", "very_high"}:
        await callback.answer("Некорректный выбор" if lang == "ru" else "Invalid choice", show_alert=True); return
    await state.update_data(activity_level=activity_level); await state.set_state(ProfileStates.goal)
    if callback.message is not None:
        await callback.message.edit_text("Какая у тебя цель?" if lang == "ru" else "What is your goal?", reply_markup=goal_keyboard(lang))
    await callback.answer()


@router.callback_query(ProfileStates.goal, F.data.startswith("profile:goal:"))
async def goal_handler(callback: CallbackQuery, state: FSMContext) -> None:
    goal = callback.data.rsplit(":", 1)[-1]
    lang = _lang(callback)
    if goal not in {"lose", "maintain", "gain"}:
        await callback.answer("Некорректный выбор" if lang == "ru" else "Invalid choice", show_alert=True); return
    data = await state.get_data(); user_id = data.get("user_id")
    if user_id is None:
        await callback.answer("Не удалось найти пользователя" if lang == "ru" else "User not found", show_alert=True); return
    await profile_service.create_profile(user_id=user_id, gender=data["gender"], age=data["age"], height_cm=data["height_cm"], weight_kg=data["weight_kg"], activity_level=data["activity_level"], goal=goal)
    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text("<b>Профиль готов! 🎉</b>" if lang == "ru" else "<b>Your profile is ready! 🎉</b>", parse_mode="HTML")
        await _render(callback, user_id)
    await callback.answer()
