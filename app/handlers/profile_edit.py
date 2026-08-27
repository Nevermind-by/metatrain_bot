from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import ProfileStates
from app.keyboards.profile import gender_keyboard, goal_keyboard, profile_keyboard
from app.keyboards.profile_edit import edit_profile_keyboard
from app.services.profile import ProfileService
from app.services.user import UserService

router = Router(name="profile_edit")
profile_service = ProfileService()
user_service = UserService()


@router.callback_query(F.data == "profile:edit")
async def edit_profile(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Что хочешь изменить?", reply_markup=edit_profile_keyboard())
    await callback.answer()


@router.callback_query(F.data == "profile:edit:gender")
async def edit_gender(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_gender)
    await callback.message.edit_text("Выбери пол:", reply_markup=gender_keyboard())
    await callback.answer()


@router.callback_query(ProfileStates.edit_gender, F.data.startswith("profile:gender:"))
async def save_gender(callback: CallbackQuery, state: FSMContext) -> None:
    await _update(callback, state, gender=callback.data.rsplit(":", 1)[-1])


@router.callback_query(F.data == "profile:edit:age")
async def edit_age(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_age)
    await callback.message.edit_text("Введи новый возраст (14–100 лет).")
    await callback.answer()


@router.message(ProfileStates.edit_age)
async def save_age(message: Message, state: FSMContext) -> None:
    try:
        value = int(message.text or "")
    except ValueError:
        await message.answer("Введи возраст целым числом, например: 28")
        return
    if not 14 <= value <= 100:
        await message.answer("Возраст должен быть от 14 до 100 лет.")
        return
    await _update_message(message, state, age=value)


@router.callback_query(F.data == "profile:edit:height")
async def edit_height(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_height)
    await callback.message.edit_text("Введи новый рост в сантиметрах (120–230).")
    await callback.answer()


@router.message(ProfileStates.edit_height)
async def save_height(message: Message, state: FSMContext) -> None:
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи рост числом, например: 180")
        return
    if not 120 <= value <= 230:
        await message.answer("Рост должен быть от 120 до 230 см.")
        return
    await _update_message(message, state, height_cm=value)


@router.callback_query(F.data == "profile:edit:weight")
async def edit_weight(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_weight)
    await callback.message.edit_text("Введи новый вес в килограммах (30–300).")
    await callback.answer()


@router.message(ProfileStates.edit_weight)
async def save_weight(message: Message, state: FSMContext) -> None:
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи вес числом, например: 80")
        return
    if not 30 <= value <= 300:
        await message.answer("Вес должен быть от 30 до 300 кг.")
        return
    await _update_message(message, state, weight_kg=value)


@router.callback_query(F.data == "profile:edit:goal")
async def edit_goal(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_goal)
    await callback.message.edit_text("Какая у тебя цель?", reply_markup=goal_keyboard())
    await callback.answer()


@router.callback_query(ProfileStates.edit_goal, F.data.startswith("profile:goal:"))
async def save_goal(callback: CallbackQuery, state: FSMContext) -> None:
    await _update(callback, state, goal=callback.data.rsplit(":", 1)[-1])


async def _load_values(telegram_id: int) -> tuple[int, dict] | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    if user is None or user.id is None:
        return None
    profile = await profile_service.get_profile(user.id)
    if profile is None:
        return None
    return user.id, {
        "gender": profile.gender,
        "age": profile.age,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "goal": profile.goal,
    }


async def _update(callback: CallbackQuery, state: FSMContext, **changes: object) -> None:
    loaded = await _load_values(callback.from_user.id)
    if loaded is None:
        await callback.answer("Профиль не найден", show_alert=True)
        return
    user_id, values = loaded
    values.update(changes)
    updated = await profile_service.update_profile(user_id, **values)
    await state.clear()
    await callback.message.edit_text("Профиль обновлён ✅\n\n" + profile_service.format_profile(updated), reply_markup=profile_keyboard())
    await callback.answer()


async def _update_message(message: Message, state: FSMContext, **changes: object) -> None:
    loaded = await _load_values(message.from_user.id)
    if loaded is None:
        await message.answer("Профиль не найден")
        await state.clear()
        return
    user_id, values = loaded
    values.update(changes)
    updated = await profile_service.update_profile(user_id, **values)
    await state.clear()
    await message.answer("Профиль обновлён ✅\n\n" + profile_service.format_profile(updated), reply_markup=profile_keyboard())
