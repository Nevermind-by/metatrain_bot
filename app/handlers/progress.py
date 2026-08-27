from aiogram import F, Router
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
    if message.from_user is None: return
    if await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start."); return
    await state.clear(); await state.set_state(WeightStates.value)
    await message.answer("Введи текущий вес в кг, например: 82.4")


@router.message(WeightStates.value)
async def weight_save(message: Message, state: FSMContext) -> None:
    try:
        weight = float((message.text or "").replace(",", ".")); user_id = await _user_id(message.from_user.id)
        if user_id is None: raise ValueError
        entry = await weight_service.add(user_id, weight)
    except ValueError:
        await message.answer("Введи вес от 30 до 300 кг, например: 82.4"); return
    await state.clear(); await message.answer(f"Вес записан ✅ {entry.weight_kg:g} кг")


@router.message(Command("weights"))
async def weights_history(message: Message) -> None:
    if message.from_user is None: return
    user_id = await _user_id(message.from_user.id)
    if user_id is None: await message.answer("Сначала создай профиль через /start."); return
    entries = await weight_service.recent(user_id)
    if not entries: await message.answer("Записей веса пока нет. Используй /weight."); return
    lines = ["⚖️ <b>Последние измерения</b>", ""]
    for entry in entries: lines.append(f"{entry.measured_at:%d.%m.%Y %H:%M} — {entry.weight_kg:g} кг")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("progress"))
async def progress_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None: return
    if await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start."); return
    await state.clear(); await state.set_state(WorkoutStates.exercise)
    await message.answer("Какое упражнение показать?\nНапример: Жим лёжа\n\n/cancel — отменить")


@router.message(WorkoutStates.exercise)
async def progress_exercise(message: Message, state: FSMContext) -> None:
    exercise = (message.text or "").strip()
    if not exercise or exercise.startswith("/"):
        return
    user_id = await _user_id(message.from_user.id) if message.from_user else None
    if user_id is None:
        await state.clear(); await message.answer("Пользователь не найден."); return
    result = await workout_service.progress(user_id, exercise)
    await state.clear()
    if not result["sets"]:
        await message.answer(f"По упражнению «{exercise}» пока нет подходов."); return
    lines = [f"📈 <b>{result['exercise']}</b>", "", f"🏆 Лучший вес: {result['best_weight']:g} кг", f"📦 Лучший подход по объёму: {result['best_volume']:g} кг", f"💪 Расчётный 1ПМ: {result['estimated_1rm']:g} кг", "", "Последние подходы:"]
    for item in result["sets"][:10]:
        rpe = f" • RPE {item.rpe:g}" if item.rpe is not None else ""
        lines.append(f"• {item.weight_kg:g} × {item.reps}{rpe}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("workout"))
async def workout_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None: return
    if await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start."); return
    await state.clear(); await state.set_state(WorkoutStates.name)
    await message.answer("Название тренировки? Например: Грудь + трицепс\n\n/cancel — отменить")


@router.message(WorkoutStates.name)
async def workout_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name: await message.answer("Введи название тренировки."); return
    user_id = await _user_id(message.from_user.id) if message.from_user else None
    if user_id is None: await state.clear(); await message.answer("Пользователь не найден."); return
    workout = await workout_service.start(user_id=user_id, name=name)
    await state.update_data(workout_id=workout.id, exercise_position=0)
    await state.set_state(WorkoutStates.exercise)
    await message.answer(f"🏋️ {workout.name}\n\nПервое упражнение? Например: Жим лёжа")


@router.message(WorkoutStates.exercise, F.text)
async def workout_exercise(message: Message, state: FSMContext) -> None:
    # Progress and workout share this state; /progress is handled before entering workout mode.
    name = (message.text or "").strip()
    if not name or name.startswith("/"): return
    data = await state.get_data()
    if "workout_id" not in data: return
    position = int(data.get("exercise_position", 0)) + 1
    exercise = await workout_service.add_exercise(workout_id=int(data["workout_id"]), name=name, position=position)
    await state.update_data(exercise_id=exercise.id, exercise_name=exercise.name, set_number=1, exercise_position=position)
    await state.set_state(WorkoutStates.weight)
    await message.answer(f"💪 {exercise.name}\nПодход 1: вес в кг?\nЕсли без веса — 0")


@router.message(WorkoutStates.weight)
async def workout_weight(message: Message, state: FSMContext) -> None:
    try: value = float((message.text or "").replace(",", "."))
    except ValueError: await message.answer("Введи вес числом, например 60 или 0."); return
    if value < 0: await message.answer("Вес не может быть отрицательным."); return
    await state.update_data(weight=value); await state.set_state(WorkoutStates.reps); await message.answer("Сколько повторений?")


@router.message(WorkoutStates.reps)
async def workout_reps(message: Message, state: FSMContext) -> None:
    try: reps = int((message.text or "").strip())
    except ValueError: await message.answer("Введи целое число повторений."); return
    if reps < 1: await message.answer("Повторения должны быть больше нуля."); return
    await state.update_data(reps=reps); await state.set_state(WorkoutStates.rpe); await message.answer("RPE от 1 до 10? Можно 0, чтобы пропустить.")


@router.message(WorkoutStates.rpe)
async def workout_rpe(message: Message, state: FSMContext) -> None:
    try: rpe = float((message.text or "").replace(",", "."))
    except ValueError: await message.answer("Введи RPE от 1 до 10 или 0."); return
    if rpe != 0 and not 1 <= rpe <= 10: await message.answer("RPE должен быть от 1 до 10, либо 0."); return
    data = await state.get_data()
    await workout_service.add_set(exercise_id=int(data["exercise_id"]), set_number=int(data["set_number"]), weight_kg=float(data["weight"]), reps=int(data["reps"]), rpe=None if rpe == 0 else rpe)
    next_set = int(data["set_number"]) + 1; await state.update_data(set_number=next_set)
    await message.answer(f"Подход {next_set}: вес в кг?\n\n/next — следующее упражнение\n/finish — закончить")


@router.message(WorkoutStates.rpe, Command("next"))
async def next_exercise(message: Message, state: FSMContext) -> None:
    await state.set_state(WorkoutStates.exercise); await message.answer("Следующее упражнение?")


@router.message(WorkoutStates.rpe, Command("finish"))
async def finish_workout(message: Message, state: FSMContext) -> None:
    await state.clear(); await message.answer("Тренировка завершена ✅\n\nИстория: /workouts")


@router.message(Command("workouts"))
async def workouts_history(message: Message) -> None:
    if message.from_user is None: return
    user_id = await _user_id(message.from_user.id)
    if user_id is None: await message.answer("Сначала создай профиль через /start."); return
    entries = await workout_service.recent(user_id)
    if not entries: await message.answer("Тренировок пока нет. Используй /workout."); return
    lines = ["🏋️ <b>Последние тренировки</b>", ""]
    for entry in entries: lines.append(f"{entry.performed_at:%d.%m.%Y} — {entry.name}")
    await message.answer("\n".join(lines), parse_mode="HTML")
