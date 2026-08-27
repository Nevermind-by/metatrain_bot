from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states import WeightStates, WorkoutStates
from app.services.user import UserService
from app.services.weight import WeightService
from app.services.workout import WorkoutService

router = Router(name="progress")
user_service = UserService()
weight_service = WeightService()
workout_service = WorkoutService()


async def _user_id(telegram_id: int) -> int | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    return user.id if user and user.id is not None else None


@router.message(Command("weight"))
async def weight_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    if await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    await state.clear()
    await state.set_state(WeightStates.value)
    await message.answer("Введи текущий вес в кг, например: 82.4")


@router.message(WeightStates.value)
async def weight_save(message: Message, state: FSMContext) -> None:
    try:
        weight = float((message.text or "").replace(",", "."))
        user_id = await _user_id(message.from_user.id)
        if user_id is None:
            raise ValueError
        entry = await weight_service.add(user_id, weight)
    except ValueError:
        await message.answer("Введи вес от 30 до 300 кг, например: 82.4")
        return
    await state.clear()
    await message.answer(f"Вес записан ✅ {entry.weight_kg:g} кг")


@router.message(Command("weights"))
async def weights_history(message: Message) -> None:
    if message.from_user is None:
        return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    entries = await weight_service.recent(user_id)
    if not entries:
        await message.answer("Записей веса пока нет. Используй /weight.")
        return
    lines = ["⚖️ <b>Последние измерения</b>", ""]
    for entry in entries:
        lines.append(f"{entry.measured_at:%d.%m.%Y %H:%M} — {entry.weight_kg:g} кг")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("workout"))
async def workout_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    if await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    await state.clear()
    await state.set_state(WorkoutStates.name)
    await message.answer("Название тренировки, например: Силовая тренировка")


@router.message(WorkoutStates.name)
async def workout_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Введи название тренировки.")
        return
    await state.update_data(name=name)
    await state.set_state(WorkoutStates.duration)
    await message.answer("Длительность в минутах. Если не хочешь указывать — напиши 0.")


@router.message(WorkoutStates.duration)
async def workout_duration(message: Message, state: FSMContext) -> None:
    try:
        value = int(message.text or "")
    except ValueError:
        await message.answer("Введи целое число минут или 0.")
        return
    if value < 0 or value > 1440:
        await message.answer("Длительность должна быть от 0 до 1440 минут.")
        return
    await state.update_data(duration_minutes=value or None)
    await state.set_state(WorkoutStates.calories)
    await message.answer("Расход калорий. Если не знаешь — напиши 0.")


@router.message(WorkoutStates.calories)
async def workout_calories(message: Message, state: FSMContext) -> None:
    try:
        value = int(message.text or "")
    except ValueError:
        await message.answer("Введи количество ккал целым числом или 0.")
        return
    if value < 0:
        await message.answer("Расход калорий не может быть отрицательным.")
        return
    await state.update_data(calories_burned=value or None)
    await state.set_state(WorkoutStates.notes)
    await message.answer("Короткая заметка или '-' если не нужна.")


@router.message(WorkoutStates.notes)
async def workout_notes(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await state.clear()
        await message.answer("Пользователь не найден. Используй /start.")
        return
    notes = None if (message.text or "").strip() in {"", "-"} else (message.text or "").strip()
    entry = await workout_service.add(
        user_id=user_id,
        name=data["name"],
        duration_minutes=data.get("duration_minutes"),
        calories_burned=data.get("calories_burned"),
        notes=notes,
    )
    await state.clear()
    await message.answer(
        f"Тренировка записана ✅\n\n{entry.name}"
        + (f" — {entry.duration_minutes} мин" if entry.duration_minutes else "")
        + (f" — {entry.calories_burned} ккал" if entry.calories_burned else "")
    )


@router.message(Command("workouts"))
async def workouts_history(message: Message) -> None:
    if message.from_user is None:
        return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    entries = await workout_service.recent(user_id)
    if not entries:
        await message.answer("Тренировок пока нет. Используй /workout.")
        return
    lines = ["🏋️ <b>Последние тренировки</b>", ""]
    for entry in entries:
        details = []
        if entry.duration_minutes:
            details.append(f"{entry.duration_minutes} мин")
        if entry.calories_burned:
            details.append(f"{entry.calories_burned} ккал")
        suffix = f" — {' • '.join(details)}" if details else ""
        lines.append(f"{entry.performed_at:%d.%m.%Y} — {entry.name}{suffix}")
    await message.answer("\n".join(lines), parse_mode="HTML")
