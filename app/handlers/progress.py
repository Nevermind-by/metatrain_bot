from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states import ProgressStates, WeightStates
from app.i18n import language_code
from app.keyboards.navigation import navigation_keyboard
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
    lang = language_code(message.from_user)
    if await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start.")
        return
    await state.clear()
    await state.set_state(WeightStates.value)
    text = "⚖️ <b>Записать вес</b>\n\nВведи текущий вес в кг, например: 82.4" if lang == "ru" else "⚖️ <b>Log weight</b>\n\nEnter your current weight in kg, for example: 82.4"
    await message.answer(text, parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))


@router.message(WeightStates.value)
async def weight_save(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    try:
        weight = float((message.text or "").replace(",", "."))
        user_id = await _user_id(message.from_user.id)
        if user_id is None:
            raise ValueError
        entry = await weight_service.add(user_id, weight)
    except ValueError:
        await message.answer("Введи вес от 30 до 300 кг, например: 82.4" if lang == "ru" else "Enter a weight between 30 and 300 kg, for example: 82.4", reply_markup=navigation_keyboard(lang=lang))
        return
    await state.clear()
    text = f"Вес записан ✅ {entry.weight_kg:g} кг" if lang == "ru" else f"Weight logged ✅ {entry.weight_kg:g} kg"
    await message.answer(text, reply_markup=navigation_keyboard(lang=lang))


@router.message(Command("weights"))
async def weights_history(message: Message) -> None:
    if message.from_user is None:
        return
    lang = language_code(message.from_user)
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start.")
        return
    entries = await weight_service.recent(user_id)
    if not entries:
        await message.answer("Записей веса пока нет. Используй /weight." if lang == "ru" else "No weight entries yet. Use /weight.", reply_markup=navigation_keyboard(lang=lang))
        return
    lines = ["⚖️ <b>Последние измерения</b>" if lang == "ru" else "⚖️ <b>Recent measurements</b>", ""]
    for entry in entries:
        unit = "кг" if lang == "ru" else "kg"
        lines.append(f"{entry.measured_at:%d.%m.%Y %H:%M} — {entry.weight_kg:g} {unit}")
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))


@router.message(Command("progress"))
async def progress_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lang = language_code(message.from_user)
    if await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start.")
        return
    await state.clear()
    await state.set_state(ProgressStates.exercise)
    text = "📈 <b>Прогресс упражнения</b>\n\nКакое упражнение показать?\nНапример: Жим лёжа" if lang == "ru" else "📈 <b>Exercise progress</b>\n\nWhich exercise should I show?\nFor example: Bench press"
    await message.answer(text, parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))


@router.message(ProgressStates.exercise)
async def progress_exercise(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    exercise = (message.text or "").strip()
    if not exercise or exercise.startswith("/"):
        return
    user_id = await _user_id(message.from_user.id) if message.from_user else None
    if user_id is None:
        await state.clear()
        await message.answer("Пользователь не найден." if lang == "ru" else "User not found.", reply_markup=navigation_keyboard(lang=lang))
        return
    result = await workout_service.progress(user_id, exercise)
    await state.clear()
    if not result["sets"]:
        text = f"По упражнению «{exercise}» пока нет подходов." if lang == "ru" else f"No sets recorded for “{exercise}” yet."
        await message.answer(text, reply_markup=navigation_keyboard(lang=lang))
        return
    if lang == "ru":
        lines = [f"📈 <b>{result['exercise']}</b>", "", f"🏆 Лучший вес: {result['best_weight']:g} кг", f"📦 Лучший подход по объёму: {result['best_volume']:g} кг", f"💪 Расчётный 1ПМ: {result['estimated_1rm']:g} кг", "", "Последние подходы:"]
    else:
        lines = [f"📈 <b>{result['exercise']}</b>", "", f"🏆 Best weight: {result['best_weight']:g} kg", f"📦 Best set by volume: {result['best_volume']:g} kg", f"💪 Estimated 1RM: {result['estimated_1rm']:g} kg", "", "Recent sets:"]
    for item in result["sets"][:10]:
        rpe = f" • RPE {item.rpe:g}" if item.rpe is not None else ""
        lines.append(f"• {item.weight_kg:g} × {item.reps}{rpe}")
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))
