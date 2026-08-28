from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import ProfileStates
from app.keyboards.navigation import navigation_keyboard
from app.keyboards.profile import activity_keyboard, gender_keyboard, goal_keyboard
from app.keyboards.profile_edit import edit_profile_keyboard
from app.keyboards.profile_edit_choices import activity_edit_keyboard, gender_edit_keyboard, goal_edit_keyboard
from app.keyboards.profile_view import profile_keyboard
from app.services.profile import ProfileService
from app.services.user import UserService

router = Router(name="profile")
profile_service = ProfileService()
user_service = UserService()


async def _load_profile(telegram_id: int):
    user = await user_service.get_by_telegram_id(telegram_id)
    if user is None or user.id is None:
        return None
    return await profile_service.get_profile(user.id)


@router.message(Command("profile"))
async def profile_handler(message: Message) -> None:
    if message.from_user is None:
        return
    profile = await _load_profile(message.from_user.id)
    if profile is None:
        await message.answer("Профиль ещё не заполнен. Используй /start.")
        return
    await message.answer(profile_service.format_profile(profile), reply_markup=profile_keyboard())


@router.callback_query(F.data == "profile:show")
async def profile_callback(callback: CallbackQuery) -> None:
    profile = await _load_profile(callback.from_user.id)
    if profile is None:
        await callback.answer("Профиль не заполнен", show_alert=True)
        return
    if callback.message is not None:
        await callback.message.edit_text(profile_service.format_profile(profile), reply_markup=profile_keyboard())
    await callback.answer()


@router.callback_query(F.data == "profile:edit")
async def edit_profile_callback(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.edit_text("Что хочешь изменить?", reply_markup=edit_profile_keyboard())
    await callback.answer()


@router.callback_query(F.data == "profile:edit:gender")
async def edit_gender_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_gender)
    if callback.message is not None:
        await callback.message.edit_text("Выбери пол:", reply_markup=gender_edit_keyboard())
    await callback.answer()


@router.callback_query(ProfileStates.edit_gender, F.data.startswith("profile:gender:"))
async def edit_gender_handler(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.rsplit(":", 1)[-1]
    if gender not in {"male", "female"}:
        await callback.answer("Некорректный выбор", show_alert=True)
        return
    await _save_edited_field(callback, state, "gender", gender)


@router.callback_query(F.data == "profile:edit:age")
async def edit_age_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_age)
    if callback.message is not None:
        await callback.message.edit_text("Введи новый возраст (14–100 лет).", reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль"))
    await callback.answer()


@router.message(ProfileStates.edit_age)
async def edit_age_handler(message: Message, state: FSMContext) -> None:
    try: age = int(message.text or "")
    except ValueError:
        await message.answer("Введи возраст целым числом, например: 28", reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль")); return
    if not 14 <= age <= 100:
        await message.answer("Возраст должен быть от 14 до 100 лет.", reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль")); return
    await _save_edited_message_field(message, state, "age", age)


@router.callback_query(F.data == "profile:edit:height")
async def edit_height_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_height)
    if callback.message is not None:
        await callback.message.edit_text("Введи новый рост в сантиметрах (120–230).", reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль"))
    await callback.answer()


@router.message(ProfileStates.edit_height)
async def edit_height_handler(message: Message, state: FSMContext) -> None:
    try: height = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи рост числом, например: 180", reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль")); return
    if not 120 <= height <= 230:
        await message.answer("Рост должен быть от 120 до 230 см.", reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль")); return
    await _save_edited_message_field(message, state, "height_cm", height)


@router.callback_query(F.data == "profile:edit:weight")
async def edit_weight_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_weight)
    if callback.message is not None:
        await callback.message.edit_text("Введи новый вес в килограммах (30–300).", reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль"))
    await callback.answer()


@router.message(ProfileStates.edit_weight)
async def edit_weight_handler(message: Message, state: FSMContext) -> None:
    try: weight = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи вес числом, например: 80", reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль")); return
    if not 30 <= weight <= 300:
        await message.answer("Вес должен быть от 30 до 300 кг.", reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль")); return
    await _save_edited_message_field(message, state, "weight_kg", weight)


@router.callback_query(F.data == "profile:edit:activity")
async def edit_activity_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_activity_level)
    if callback.message is not None:
        await callback.message.edit_text("Выбери уровень активности:", reply_markup=activity_edit_keyboard())
    await callback.answer()


@router.callback_query(ProfileStates.edit_activity_level, F.data.startswith("profile:activity:"))
async def edit_activity_handler(callback: CallbackQuery, state: FSMContext) -> None:
    activity = callback.data.rsplit(":", 1)[-1]
    if activity not in {"sedentary", "light", "moderate", "high", "very_high"}:
        await callback.answer("Некорректный выбор", show_alert=True); return
    await _save_edited_field(callback, state, "activity_level", activity)


@router.callback_query(F.data == "profile:edit:goal")
async def edit_goal_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_goal)
    if callback.message is not None:
        await callback.message.edit_text("Какая у тебя цель?", reply_markup=goal_edit_keyboard())
    await callback.answer()


@router.callback_query(ProfileStates.edit_goal, F.data.startswith("profile:goal:"))
async def edit_goal_handler(callback: CallbackQuery, state: FSMContext) -> None:
    goal = callback.data.rsplit(":", 1)[-1]
    if goal not in {"lose", "maintain", "gain"}:
        await callback.answer("Некорректный выбор", show_alert=True); return
    await _save_edited_field(callback, state, "goal", goal)


async def _save_values(telegram_id: int, field: str, value: object):
    user = await user_service.get_by_telegram_id(telegram_id)
    if user is None or user.id is None: raise LookupError("User not found")
    profile = await profile_service.get_profile(user.id)
    if profile is None: raise LookupError("Profile not found")
    values = {"gender": profile.gender, "age": profile.age, "height_cm": profile.height_cm, "weight_kg": profile.weight_kg, "activity_level": profile.activity_level, "goal": profile.goal}
    values[field] = value
    return await profile_service.update_profile(user.id, **values)


async def _save_edited_field(callback: CallbackQuery, state: FSMContext, field: str, value: object) -> None:
    try: updated = await _save_values(callback.from_user.id, field, value)
    except LookupError as error:
        await callback.answer(str(error), show_alert=True); return
    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text("Профиль обновлён ✅\n\n" + profile_service.format_profile(updated), reply_markup=profile_keyboard())
    await callback.answer()


async def _save_edited_message_field(message: Message, state: FSMContext, field: str, value: object) -> None:
    try: updated = await _save_values(message.from_user.id, field, value)
    except LookupError as error:
        await message.answer(str(error), reply_markup=navigation_keyboard(back_callback="profile:show", back_text="◀️ Профиль")); await state.clear(); return
    await state.clear()
    await message.answer("Профиль обновлён ✅\n\n" + profile_service.format_profile(updated), reply_markup=profile_keyboard())
