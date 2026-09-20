from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import ProgressStates, WeightStates
from app.i18n import language_code
from app.keyboards.navigation import navigation_keyboard
from app.keyboards.progress import (
    progress_categories,
    progress_exercise_list,
    progress_search_results,
)
from app.services.exercise_catalog import ExerciseCatalogService
from app.services.user import UserService
from app.services.weight import WeightService
from app.services.workout import WorkoutService

router = Router(name="progress")
user_service = UserService()
weight_service = WeightService()
workout_service = WorkoutService()
exercise_catalog = ExerciseCatalogService()


async def _user_id(telegram_id: int) -> int | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    return user.id if user and user.id is not None else None


@router.message(Command("weight"))
async def weight_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lang = language_code(message.from_user)
    if await _user_id(message.from_user.id) is None:
        await message.answer(
            "Сначала создай профиль через /start."
            if lang == "ru"
            else "Create your profile with /start."
        )
        return
    await state.clear()
    await state.set_state(WeightStates.value)
    text = (
        "⚖️ <b>Записать вес</b>\n\nВведи текущий вес в кг, например: 82.4"
        if lang == "ru"
        else "⚖️ <b>Log weight</b>\n\nEnter your current weight in kg, for example: 82.4"
    )
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
        await message.answer(
            "Введи вес от 30 до 300 кг, например: 82.4"
            if lang == "ru"
            else "Enter a weight between 30 and 300 kg, for example: 82.4",
            reply_markup=navigation_keyboard(lang=lang),
        )
        return
    await state.clear()
    text = (
        f"Вес записан ✅ {entry.weight_kg:g} кг"
        if lang == "ru"
        else f"Weight logged ✅ {entry.weight_kg:g} kg"
    )
    await message.answer(text, reply_markup=navigation_keyboard(lang=lang))


@router.message(Command("weights"))
async def weights_history(message: Message) -> None:
    if message.from_user is None:
        return
    lang = language_code(message.from_user)
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer(
            "Сначала создай профиль через /start."
            if lang == "ru"
            else "Create your profile with /start."
        )
        return
    entries = await weight_service.recent(user_id)
    if not entries:
        await message.answer(
            "Записей веса пока нет. Используй /weight."
            if lang == "ru"
            else "No weight entries yet. Use /weight.",
            reply_markup=navigation_keyboard(lang=lang),
        )
        return
    lines = [
        "⚖️ <b>Последние измерения</b>" if lang == "ru" else "⚖️ <b>Recent measurements</b>",
        "",
    ]
    for entry in entries:
        unit = "кг" if lang == "ru" else "kg"
        lines.append(f"{entry.measured_at:%d.%m.%Y %H:%M} — {entry.weight_kg:g} {unit}")
    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=navigation_keyboard(lang=lang),
    )


def _progress_menu_text(lang: str) -> str:
    return (
        "📈 <b>Прогресс упражнения</b>\n\nВыбери группу мышц или найди упражнение:"
        if lang == "ru"
        else "📈 <b>Exercise progress</b>\n\nChoose a muscle group or search for an exercise:"
    )


async def _show_progress(target: Message | CallbackQuery, state: FSMContext, exercise_name: str) -> None:
    lang = language_code(target.from_user)
    user_id = await _user_id(target.from_user.id)
    if user_id is None:
        await state.clear()
        if isinstance(target, CallbackQuery):
            await target.answer(
                "Пользователь не найден." if lang == "ru" else "User not found.",
                show_alert=True,
            )
        return

    result = await workout_service.progress(user_id, exercise_name)
    await state.clear()

    if not result["sets"]:
        text = (
            f"По упражнению «{exercise_name}» пока нет подходов."
            if lang == "ru"
            else f"No sets recorded for “{exercise_name}” yet."
        )
        markup = navigation_keyboard(lang=lang, back_callback="progress:menu")
    else:
        if lang == "ru":
            lines = [
                f"📈 <b>{result['exercise']}</b>",
                "",
                f"🏆 Лучший вес: {result['best_weight']:g} кг",
                f"📦 Лучший подход по объёму: {result['best_volume']:g} кг",
                f"💪 Расчётный 1ПМ: {result['estimated_1rm']:g} кг",
                "",
                "Последние подходы:",
            ]
        else:
            lines = [
                f"📈 <b>{result['exercise']}</b>",
                "",
                f"🏆 Best weight: {result['best_weight']:g} kg",
                f"📦 Best set by volume: {result['best_volume']:g} kg",
                f"💪 Estimated 1RM: {result['estimated_1rm']:g} kg",
                "",
                "Recent sets:",
            ]
        for item in result["sets"][:10]:
            rpe = f" • RPE {item.rpe:g}" if item.rpe is not None else ""
            lines.append(f"• {item.weight_kg:g} × {item.reps}{rpe}")
        if result["sessions"]:
            lines.extend(["", "Последние тренировки:" if lang == "ru" else "Recent workouts:"])
            for session in result["sessions"][:5]:
                performed = session["performed_at"]
                try:
                    label = performed[8:10] + "." + performed[5:7] + "." + performed[:4]
                except (TypeError, IndexError):
                    label = str(performed)[:10]
                lines.append(
                    f"• {label} — {session['max_weight']:g} кг · {session['volume']:g} кг"
                    if lang == "ru"
                    else f"• {label} — {session['max_weight']:g} kg · {session['volume']:g} kg"
                )
        text = "\n".join(lines)
        markup = navigation_keyboard(lang=lang, back_callback="progress:menu")

    if isinstance(target, CallbackQuery):
        if target.message is not None:
            await target.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=markup)


@router.message(Command("progress"))
async def progress_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lang = language_code(message.from_user)
    if await _user_id(message.from_user.id) is None:
        await message.answer(
            "Сначала создай профиль через /start."
            if lang == "ru"
            else "Create your profile with /start."
        )
        return
    await state.clear()
    await state.set_state(ProgressStates.exercise)
    await message.answer(
        _progress_menu_text(lang),
        parse_mode="HTML",
        reply_markup=progress_categories(lang),
    )


@router.callback_query(F.data == "progress:menu")
async def progress_menu(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    await state.set_state(ProgressStates.exercise)
    if callback.message is not None:
        await callback.message.edit_text(
            _progress_menu_text(lang),
            parse_mode="HTML",
            reply_markup=progress_categories(lang),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("progress:category:"))
async def progress_category(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    category = callback.data.rsplit(":", 1)[-1]
    items = await exercise_catalog.list_by_category(category)
    await state.set_state(ProgressStates.exercise)
    if callback.message is not None:
        await callback.message.edit_text(
            "Выбери упражнение:" if lang == "ru" else "Choose an exercise:",
            reply_markup=progress_exercise_list(items, lang),
        )
    await callback.answer()


@router.callback_query(F.data == "progress:search")
async def progress_search(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    await state.set_state(ProgressStates.exercise)
    if callback.message is not None:
        await callback.message.edit_text(
            "🔎 <b>Поиск упражнения</b>\n\nНапиши название, например: жим лёжа"
            if lang == "ru"
            else "🔎 <b>Find an exercise</b>\n\nEnter a name, for example: bench press",
            parse_mode="HTML",
            reply_markup=navigation_keyboard(
                lang=lang,
                back_callback="progress:menu",
                back_text="⬅️ Группы" if lang == "ru" else "⬅️ Muscle groups",
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("progress:exercise:"))
async def progress_exercise_selected(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.rsplit(":", 1)[-1]
    lang = language_code(callback.from_user)
    if not value.isdigit():
        await callback.answer(
            "Некорректное упражнение" if lang == "ru" else "Invalid exercise",
            show_alert=True,
        )
        return
    item = await exercise_catalog.get(int(value))
    if item is None:
        await callback.answer(
            "Упражнение не найдено" if lang == "ru" else "Exercise not found",
            show_alert=True,
        )
        return
    exercise_name = item.name_ru if lang == "ru" else item.name_en
    await _show_progress(callback, state, exercise_name)
    await callback.answer()


@router.message(ProgressStates.exercise)
async def progress_exercise(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    query = (message.text or "").strip()
    if not query or query.startswith("/"):
        return
    items = await exercise_catalog.search(query, limit=12)
    if not items:
        await message.answer(
            "Ничего не нашёл. Попробуй другое название."
            if lang == "ru"
            else "Nothing found. Try another name.",
            reply_markup=progress_categories(lang),
        )
        return
    await message.answer(
        (
            f"🔎 <b>Результаты для «{query}»</b>\n\nВыбери упражнение:"
            if lang == "ru"
            else f"🔎 <b>Results for “{query}”</b>\n\nChoose an exercise:"
        ),
        parse_mode="HTML",
        reply_markup=progress_search_results(items, lang),
    )
