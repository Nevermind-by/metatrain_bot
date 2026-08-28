from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import WorkoutStates
from app.i18n import language_code
from app.keyboards.exercise import (
    exercise_categories,
    exercise_list,
    exercise_search_result,
    previous_set_keyboard,
    workout_set_keyboard,
)
from app.keyboards.navigation import navigation_keyboard
from app.keyboards.main_menu import main_menu_texts
from app.services.exercise_catalog import ExerciseCatalogService
from app.services.user import UserService
from app.services.workout import WorkoutService

router = Router(name="workout_session")
user_service = UserService()
workout_service = WorkoutService()
exercise_catalog = ExerciseCatalogService()


def _matches_workout_menu(message: Message) -> bool:
    if not message.text:
        return False
    return message.text in {main_menu_texts("ru")["workout"], main_menu_texts("en")["workout"]}


async def _user_id(telegram_id: int) -> int | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    return user.id if user and user.id is not None else None


async def open_workout_menu(
    message: Message | CallbackQuery,
    state: FSMContext,
    *,
    continue_session: bool = False,
) -> None:
    lang = language_code(message.from_user)
    data = await state.get_data() if continue_session else {}
    if not continue_session:
        await state.clear()
    await state.set_state(WorkoutStates.category)

    active = bool(data.get("workout_id"))
    if lang == "ru":
        text = (
            "🏋️ <b>Продолжим тренировку</b>\n\nВыбери следующее упражнение или найди его:"
            if active
            else "🏋️ <b>Новая тренировка</b>\n\nВыбери группу мышц или найди упражнение:"
        )
    else:
        text = (
            "🏋️ <b>Continue workout</b>\n\nChoose the next exercise or search for one:"
            if active
            else "🏋️ <b>New workout</b>\n\nChoose a muscle group or search for an exercise:"
        )
    markup = exercise_categories(lang)
    if isinstance(message, CallbackQuery):
        if message.message is not None:
            await message.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=markup)


@router.message(_matches_workout_menu)
async def workout_main_menu(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lang = language_code(message)
    if await _user_id(message.from_user.id) is None:
        await message.answer(
            "Сначала создай профиль через /start."
            if lang == "ru"
            else "Create your profile with /start first."
        )
        return
    await open_workout_menu(message, state)


@router.message(Command("workout"))
async def workout_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lang = language_code(message)
    if await _user_id(message.from_user.id) is None:
        await message.answer(
            "Сначала создай профиль через /start."
            if lang == "ru"
            else "Create your profile with /start first."
        )
        return
    await open_workout_menu(message, state)


@router.callback_query(F.data == "dashboard:workout")
async def dashboard_workout(callback: CallbackQuery, state: FSMContext) -> None:
    await open_workout_menu(callback, state)
    await callback.answer()


@router.callback_query(F.data == "workout:menu")
async def workout_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await open_workout_menu(callback, state, continue_session=True)
    await callback.answer()


@router.callback_query(F.data.startswith("workout:category:"))
async def workout_category(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    category = callback.data.rsplit(":", 1)[-1]
    items = await exercise_catalog.list_by_category(category)
    await state.set_state(WorkoutStates.exercise)
    if callback.message is not None:
        title = "Выбери упражнение:" if lang == "ru" else "Choose an exercise:"
        await callback.message.edit_text(title, reply_markup=exercise_list(items, lang, category))
    await callback.answer()


@router.callback_query(F.data == "workout:search")
async def workout_search_start(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    await state.set_state(WorkoutStates.exercise)
    text = (
        "🔎 <b>Поиск упражнения</b>\n\nНапиши название, например: жим лёжа"
        if lang == "ru"
        else "🔎 <b>Find an exercise</b>\n\nEnter a name, for example: bench press"
    )
    if callback.message is not None:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=navigation_keyboard(
                lang=lang,
                back_callback="workout:menu",
                back_text="⬅️ Группы" if lang == "ru" else "⬅️ Muscle groups",
            ),
        )
    await callback.answer()


@router.message(WorkoutStates.exercise)
async def workout_exercise_message(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    lang = language_code(message)
    if not text or text.startswith("/"):
        return
    items = await exercise_catalog.search(text, limit=12)
    if not items:
        await message.answer(
            "Ничего не нашёл. Попробуй другое название."
            if lang == "ru"
            else "Nothing found. Try another name.",
            reply_markup=navigation_keyboard(
                lang=lang,
                back_callback="workout:menu",
                back_text="⬅️ Группы" if lang == "ru" else "⬅️ Muscle groups",
            ),
        )
        return
    title = (
        f"🔎 <b>Результаты для «{text}»</b>\n\nВыбери упражнение:"
        if lang == "ru"
        else f"🔎 <b>Results for “{text}”</b>\n\nChoose an exercise:"
    )
    await message.answer(title, parse_mode="HTML", reply_markup=exercise_search_result(items, lang))


async def _show_first_set_prompt(
    callback: CallbackQuery,
    state: FSMContext,
    exercise_name: str,
    user_id: int,
) -> None:
    lang = language_code(callback.from_user)
    previous = await workout_service.latest_set_for_exercise(user_id, exercise_name)
    set_number = 1
    data = await state.get_data()
    if previous is not None:
        await state.update_data(previous_weight=previous.weight_kg, previous_reps=previous.reps)
        text = (
            f"🏋️ <b>{exercise_name}</b>\n\nПодход 1\nПоследний раз: {previous.weight_kg:g} кг × {previous.reps}"
            if lang == "ru"
            else f"🏋️ <b>{exercise_name}</b>\n\nSet 1\nLast time: {previous.weight_kg:g} kg × {previous.reps}"
        )
        markup = previous_set_keyboard(previous.weight_kg, previous.reps, lang)
    else:
        text = (
            f"🏋️ <b>{exercise_name}</b>\n\nПодход {set_number}\nВес, кг:"
            if lang == "ru"
            else f"🏋️ <b>{exercise_name}</b>\n\nSet {set_number}\nWeight, kg:"
        )
        markup = navigation_keyboard(lang=lang)
    if callback.message is not None:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)


async def _start_selected_exercise(
    callback: CallbackQuery,
    state: FSMContext,
    exercise_id: int,
) -> None:
    lang = language_code(callback.from_user)
    user_id = await _user_id(callback.from_user.id)
    if user_id is None:
        await callback.answer("Профиль не найден" if lang == "ru" else "Profile not found", show_alert=True)
        return
    item = await exercise_catalog.get(exercise_id)
    if item is None:
        await callback.answer("Упражнение не найдено" if lang == "ru" else "Exercise not found", show_alert=True)
        return

    data = await state.get_data()
    workout_id = data.get("workout_id")
    position = int(data.get("exercise_position", 0)) + 1
    if workout_id is None:
        workout_name = "Силовая тренировка" if lang == "ru" else "Strength workout"
        workout = await workout_service.start(user_id=user_id, name=workout_name)
        workout_id = workout.id
        position = 1

    exercise = await workout_service.add_exercise(
        workout_id=int(workout_id),
        name=item.name_ru if lang == "ru" else item.name_en,
        position=position,
    )
    await state.update_data(
        workout_id=int(workout_id),
        exercise_id=exercise.id,
        exercise_name=exercise.name,
        set_number=1,
        exercise_position=position,
    )
    await state.set_state(WorkoutStates.weight)
    await _show_first_set_prompt(callback, state, exercise.name, user_id)


@router.callback_query(F.data.startswith("workout:exercise:"))
async def workout_exercise_selected(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.rsplit(":", 1)[-1]
    if not value.isdigit():
        await callback.answer("Некорректное упражнение", show_alert=True)
        return
    await _start_selected_exercise(callback, state, int(value))
    await callback.answer()


@router.callback_query(F.data == "workout:set:repeat")
async def workout_repeat_previous(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    data = await state.get_data()
    weight = data.get("previous_weight")
    reps = data.get("previous_reps")
    if weight is None or reps is None:
        await callback.answer("Предыдущих данных нет" if lang == "ru" else "No previous data", show_alert=True)
        return
    await state.update_data(weight=float(weight), reps=int(reps))
    await state.set_state(WorkoutStates.rpe)
    text = (
        "✅ Вес и повторения перенесены. Укажи RPE от 1 до 10 или 0, чтобы пропустить."
        if lang == "ru"
        else "✅ Previous weight and reps copied. Enter RPE from 1 to 10, or 0 to skip."
    )
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()


@router.callback_query(F.data == "workout:set:manual")
async def workout_manual_set(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    data = await state.get_data()
    set_number = int(data.get("set_number", 1))
    await state.set_state(WorkoutStates.weight)
    if callback.message is not None:
        await callback.message.edit_text(
            f"Подход {set_number}\n\nВес, кг:" if lang == "ru" else f"Set {set_number}\n\nWeight, kg:",
            reply_markup=navigation_keyboard(lang=lang),
        )
    await callback.answer()


@router.message(WorkoutStates.weight)
async def workout_weight(message: Message, state: FSMContext) -> None:
    lang = language_code(message)
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer(
            "Введи вес числом, например 60 или 0."
            if lang == "ru"
            else "Enter a weight, for example 60 or 0.",
            reply_markup=navigation_keyboard(lang=lang),
        )
        return
    if value < 0:
        await message.answer(
            "Вес не может быть отрицательным."
            if lang == "ru"
            else "Weight cannot be negative.",
            reply_markup=navigation_keyboard(lang=lang),
        )
        return
    await state.update_data(weight=value)
    await state.set_state(WorkoutStates.reps)
    await message.answer(
        "Сколько повторений?" if lang == "ru" else "How many reps?",
        reply_markup=navigation_keyboard(lang=lang),
    )


@router.message(WorkoutStates.reps)
async def workout_reps(message: Message, state: FSMContext) -> None:
    lang = language_code(message)
    try:
        reps = int((message.text or "").strip())
    except ValueError:
        await message.answer(
            "Введи целое число повторений." if lang == "ru" else "Enter a whole number of reps.",
            reply_markup=navigation_keyboard(lang=lang),
        )
        return
    if reps < 1:
        await message.answer(
            "Повторения должны быть больше нуля." if lang == "ru" else "Reps must be greater than zero.",
            reply_markup=navigation_keyboard(lang=lang),
        )
        return
    await state.update_data(reps=reps)
    await state.set_state(WorkoutStates.rpe)
    await message.answer(
        "RPE от 1 до 10? Можно 0, чтобы пропустить."
        if lang == "ru"
        else "RPE from 1 to 10? Enter 0 to skip.",
        reply_markup=navigation_keyboard(lang=lang),
    )


@router.message(WorkoutStates.rpe)
async def workout_rpe(message: Message, state: FSMContext) -> None:
    lang = language_code(message)
    text = (message.text or "").strip()
    try:
        rpe = float(text.replace(",", "."))
    except ValueError:
        await message.answer(
            "Введи RPE от 1 до 10 или 0." if lang == "ru" else "Enter an RPE from 1 to 10 or 0.",
            reply_markup=navigation_keyboard(lang=lang),
        )
        return
    if rpe != 0 and not 1 <= rpe <= 10:
        await message.answer(
            "RPE должен быть от 1 до 10, либо 0."
            if lang == "ru"
            else "RPE must be from 1 to 10, or 0.",
            reply_markup=navigation_keyboard(lang=lang),
        )
        return

    data = await state.get_data()
    await workout_service.add_set(
        exercise_id=int(data["exercise_id"]),
        set_number=int(data["set_number"]),
        weight_kg=float(data["weight"]),
        reps=int(data["reps"]),
        rpe=None if rpe == 0 else rpe,
    )
    next_set = int(data["set_number"]) + 1
    await state.update_data(set_number=next_set)
    text = (
        f"✅ Подход {next_set - 1} записан.\n\nЧто дальше?"
        if lang == "ru"
        else f"✅ Set {next_set - 1} saved.\n\nWhat next?"
    )
    await message.answer(text, reply_markup=workout_set_keyboard(lang))


@router.callback_query(F.data == "workout:set:next")
async def workout_next_set(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    await state.set_state(WorkoutStates.weight)
    data = await state.get_data()
    set_number = int(data.get("set_number", 1))
    if callback.message is not None:
        await callback.message.edit_text(
            f"Подход {set_number}\n\nВес, кг:" if lang == "ru" else f"Set {set_number}\n\nWeight, kg:",
            reply_markup=navigation_keyboard(lang=lang),
        )
    await callback.answer()


@router.callback_query(F.data == "workout:finish")
async def workout_finish(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    data = await state.get_data()
    user_id = await _user_id(callback.from_user.id)
    workout_id = data.get("workout_id")
    if user_id is not None and workout_id:
        await workout_service.complete(user_id=user_id, workout_id=int(workout_id))
    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text(
            "Тренировка завершена ✅" if lang == "ru" else "Workout finished ✅",
            reply_markup=navigation_keyboard(lang=lang),
        )
    await callback.answer()


@router.message(Command("cancel"))
async def workout_cancel(message: Message, state: FSMContext) -> None:
    lang = language_code(message)
    await state.clear()
    await message.answer(
        "Тренировка отменена." if lang == "ru" else "Workout cancelled.",
        reply_markup=navigation_keyboard(lang=lang),
    )


@router.message(Command("workouts"))
async def workouts(message: Message) -> None:
    lang = language_code(message)
    if message.from_user is None:
        return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer(
            "Сначала создай профиль через /start."
            if lang == "ru"
            else "Create your profile with /start first."
        )
        return
    entries = await workout_service.recent(user_id)
    if not entries:
        await message.answer(
            "Тренировок пока нет. Открой «Тренировка» с дашборда."
            if lang == "ru"
            else "No workouts yet. Open Workout from the dashboard.",
            reply_markup=navigation_keyboard(lang=lang),
        )
        return
    lines = [
        "🏋️ <b>Последние тренировки</b>" if lang == "ru" else "🏋️ <b>Recent workouts</b>",
        "",
    ]
    for item in entries:
        lines.append(f"#{item.id} {item.name} — {item.performed_at.strftime('%d.%m.%Y %H:%M')}")
    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=navigation_keyboard(lang=lang),
    )
