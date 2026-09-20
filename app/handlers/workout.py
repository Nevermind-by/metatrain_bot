from datetime import UTC, datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import WorkoutStates
from app.i18n import language_code
from app.keyboards.dashboard import dashboard_keyboard
from app.keyboards.exercise import current_exercise_keyboard, current_workout_keyboard, delete_set_confirmation_keyboard, exercise_categories, exercise_list, exercise_search_result, previous_set_keyboard, workout_set_keyboard
from app.keyboards.navigation import navigation_keyboard
from app.services.exercise_catalog import ExerciseCatalogService
from app.services.user import UserService
from app.services.workout import WorkoutService

router = Router(name="workout")
user_service = UserService()
workout_service = WorkoutService()
exercise_catalog = ExerciseCatalogService()

async def _user_id(telegram_id: int) -> int | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    return user.id if user and user.id is not None else None

async def open_workout_menu(message: Message | CallbackQuery, state: FSMContext, *, preserve_session: bool = False) -> None:
    lang = language_code(message.from_user)
    data = await state.get_data() if preserve_session else {}
    if not preserve_session:
        user_id = await _user_id(message.from_user.id)
        active = await workout_service.active_for_user(user_id) if user_id is not None else None
        await state.clear()
        if active is not None and active.id is not None:
            data = {"workout_id": active.id}
            await state.update_data(**data)
    else:
        if data.get("workout_id") is None:
            user_id = await _user_id(message.from_user.id)
            active = await workout_service.active_for_user(user_id) if user_id is not None else None
            if active is not None and active.id is not None:
                data["workout_id"] = active.id
                await state.update_data(workout_id=active.id)
    await state.set_state(WorkoutStates.category)
    text = (("🏋️ <b>Добавить упражнение</b>\n\nВыбери группу мышц или найди упражнение:" if lang == "ru" else "🏋️ <b>Add exercise</b>\n\nChoose a muscle group or search for an exercise:") if data.get("workout_id") else ("🏋️ <b>Новая тренировка</b>\n\nВыбери группу мышц или найди упражнение:" if lang == "ru" else "🏋️ <b>New workout</b>\n\nChoose a muscle group or search for an exercise:"))
    markup = exercise_categories(lang)
    if isinstance(message, CallbackQuery):
        if message.message is not None:
            await message.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=markup)

async def _show_current_workout(target: Message | CallbackQuery, state: FSMContext) -> None:
    lang = language_code(target.from_user)
    data = await state.get_data()
    workout_id = data.get("workout_id")
    user_id = await _user_id(target.from_user.id)
    if user_id is not None and not workout_id:
        active = await workout_service.active_for_user(user_id)
        if active is not None and active.id is not None:
            workout_id = active.id
            await state.update_data(workout_id=workout_id)
    if not workout_id or user_id is None:
        text = "Активной тренировки нет." if lang == "ru" else "There is no active workout."
        markup = navigation_keyboard(lang=lang)
    else:
        workout = await workout_service.get_workout_for_user(int(workout_id), user_id)
        entries = await workout_service.repository.exercises_with_sets_for_workout(int(workout_id)) if workout else []
        elapsed_minutes = max(0, int((datetime.now(UTC) - workout.performed_at).total_seconds() // 60)) if workout else 0
        lines = ["📋 <b>Текущая тренировка</b>", f"⏱ Время: {elapsed_minutes} мин", ""] if lang == "ru" else ["📋 <b>Current workout</b>", f"⏱ Duration: {elapsed_minutes} min", ""]
        if not entries:
            lines.append("Пока нет упражнений." if lang == "ru" else "No exercises yet.")
        for exercise, sets in entries:
            suffix = "подх." if lang == "ru" else "sets"
            lines.append(f"• <b>{exercise.name}</b> — {len(sets)} {suffix}")
            for index, item in enumerate(sets, 1):
                rpe = f" · RPE {item.rpe:g}" if item.rpe is not None else ""
                lines.append(f"  {index}. {item.weight_kg:g} кг × {item.reps}{rpe}" if lang == "ru" else f"  {index}. {item.weight_kg:g} kg × {item.reps}{rpe}")
        text = "\n".join(lines)
        markup = current_workout_keyboard(lang, [(exercise.id, exercise.name) for exercise, _ in entries])
    if isinstance(target, CallbackQuery):
        if target.message is not None:
            await target.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=markup)

@router.message(Command("workout"))
async def workout_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None: return
    if await _user_id(message.from_user.id) is None:
        lang = language_code(message)
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start first.")
        return
    await open_workout_menu(message, state)

@router.callback_query(F.data == "workout:menu")
async def workout_menu(callback: CallbackQuery, state: FSMContext) -> None:
    preserve_session = bool((await state.get_data()).get("workout_id"))
    await open_workout_menu(callback, state, preserve_session=preserve_session)
    await callback.answer()

@router.callback_query(F.data == "workout:add")
async def workout_add(callback: CallbackQuery, state: FSMContext) -> None:
    await open_workout_menu(callback, state, preserve_session=True)
    await callback.answer()

@router.callback_query(F.data == "workout:current")
async def workout_current(callback: CallbackQuery, state: FSMContext) -> None:
    await _show_current_workout(callback, state)
    await callback.answer()

async def _render_current_exercise(target: Message | CallbackQuery, state: FSMContext, exercise_id: int, user_id: int) -> None:
    lang = language_code(target.from_user)
    exercise = await workout_service.get_exercise_for_user(exercise_id, user_id)
    if exercise is None:
        if isinstance(target, CallbackQuery):
            await target.answer("Упражнение не найдено" if lang == "ru" else "Exercise not found", show_alert=True)
        else:
            await target.answer("Упражнение не найдено" if lang == "ru" else "Exercise not found")
        return
    sets = await workout_service.repository.sets_for_exercise(exercise.id)
    lines = [f"🏋️ <b>{exercise.name}</b>", ""]
    if sets:
        for index, item in enumerate(sets, 1):
            rpe = f" · RPE {item.rpe:g}" if item.rpe is not None else ""
            lines.append(f"{index}. {item.weight_kg:g} кг × {item.reps}{rpe}" if lang == "ru" else f"{index}. {item.weight_kg:g} kg × {item.reps}{rpe}")
    else:
        lines.append("Подходов пока нет." if lang == "ru" else "No sets yet.")
    markup = current_exercise_keyboard([s.id for s in sets if s.id is not None], lang)
    if isinstance(target, CallbackQuery):
        if target.message is not None:
            await target.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=markup)
    else:
        await target.answer("\n".join(lines), parse_mode="HTML", reply_markup=markup)
    await state.update_data(exercise_id=exercise.id, exercise_name=exercise.name, set_number=len(sets) + 1, editing_set_id=None, editing_rpe=None)


@router.callback_query(F.data.startswith("workout:current:exercise:"))
async def workout_current_exercise(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    user_id = await _user_id(callback.from_user.id)
    value = callback.data.rsplit(":", 1)[-1]
    if user_id is None or not value.isdigit():
        await callback.answer("Некорректное упражнение" if lang == "ru" else "Invalid exercise", show_alert=True)
        return
    await _render_current_exercise(callback, state, int(value), user_id)
    await callback.answer()


@router.callback_query(F.data.startswith("workout:set:edit:"))
async def workout_edit_set(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    user_id = await _user_id(callback.from_user.id)
    value = callback.data.rsplit(":", 1)[-1]
    if user_id is None or not value.isdigit():
        await callback.answer("Некорректный подход" if lang == "ru" else "Invalid set", show_alert=True)
        return
    item = await workout_service.repository.get_set_for_user(int(value), user_id)
    if item is None:
        await callback.answer("Подход не найден" if lang == "ru" else "Set not found", show_alert=True)
        return
    await state.update_data(editing_set_id=item.id, weight=item.weight_kg, reps=item.reps, editing_rpe=item.rpe)
    await state.set_state(WorkoutStates.weight)
    if callback.message is not None:
        text = f"✏️ <b>Редактирование подхода {item.set_number}</b>\n\nТекущие данные: {item.weight_kg:g} кг × {item.reps}" if lang == "ru" else f"✏️ <b>Edit set {item.set_number}</b>\n\nCurrent: {item.weight_kg:g} kg × {item.reps}"
        await callback.message.edit_text(text + ("\n\nВведи новый вес, кг:" if lang == "ru" else "\n\nEnter new weight, kg:"), parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()


@router.callback_query(F.data.regexp(r"^workout:set:delete:\d+$"))
async def workout_delete_set(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    user_id = await _user_id(callback.from_user.id)
    value = callback.data.rsplit(":", 1)[-1]
    if user_id is None or not value.isdigit():
        await callback.answer("Некорректный подход" if lang == "ru" else "Invalid set", show_alert=True)
        return
    item = await workout_service.repository.get_set_for_user(int(value), user_id)
    if item is None:
        await callback.answer("Подход не найден" if lang == "ru" else "Set not found", show_alert=True)
        return
    await state.update_data(exercise_id=item.exercise_id)
    if callback.message is not None:
        text = f"Удалить подход {item.set_number}: {item.weight_kg:g} кг × {item.reps}?" if lang == "ru" else f"Delete set {item.set_number}: {item.weight_kg:g} kg × {item.reps}?"
        await callback.message.edit_text(text, reply_markup=delete_set_confirmation_keyboard(item.id, lang))
    await callback.answer()


@router.callback_query(F.data.startswith("workout:set:delete:confirm:"))
async def workout_delete_set_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    user_id = await _user_id(callback.from_user.id)
    value = callback.data.rsplit(":", 1)[-1]
    if user_id is None or not value.isdigit():
        await callback.answer("Некорректный подход" if lang == "ru" else "Invalid set", show_alert=True)
        return
    deleted = await workout_service.delete_set(set_id=int(value), user_id=user_id)
    if not deleted:
        await callback.answer("Подход не найден" if lang == "ru" else "Set not found", show_alert=True)
        return
    data = await state.get_data()
    exercise_id = data.get("exercise_id")
    if exercise_id:
        await _render_current_exercise(callback, state, int(exercise_id), user_id)
    await callback.answer("Удалено" if lang == "ru" else "Deleted")


@router.callback_query(F.data == "workout:set:delete:cancel")
async def workout_delete_set_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    user_id = await _user_id(callback.from_user.id)
    data = await state.get_data()
    exercise_id = data.get("exercise_id")
    if user_id is not None and exercise_id:
        await _render_current_exercise(callback, state, int(exercise_id), user_id)
    else:
        if callback.message is not None:
            await callback.message.edit_text("Удаление отменено." if lang == "ru" else "Deletion cancelled.", reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()

@router.callback_query(F.data.startswith("workout:category:"))
async def workout_category(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    category = callback.data.rsplit(":", 1)[-1]
    items = await exercise_catalog.list_by_category(category)
    await state.set_state(WorkoutStates.exercise)
    if callback.message is not None:
        await callback.message.edit_text("Выбери упражнение:" if lang == "ru" else "Choose an exercise:", reply_markup=exercise_list(items, lang, category))
    await callback.answer()

@router.callback_query(F.data == "workout:search")
async def workout_search_start(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    await state.set_state(WorkoutStates.exercise)
    if callback.message is not None:
        text = "🔎 <b>Поиск упражнения</b>\n\nНапиши название, например: жим лёжа" if lang == "ru" else "🔎 <b>Find an exercise</b>\n\nEnter a name, for example: bench press"
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang, back_callback="workout:menu", back_text="⬅️ Группы" if lang == "ru" else "⬅️ Muscle groups"))
    await callback.answer()

@router.message(WorkoutStates.exercise)
async def workout_exercise_message(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip(); lang = language_code(message)
    if not text or text.startswith("/"): return
    items = await exercise_catalog.search(text, limit=12)
    if not items:
        await message.answer("Ничего не нашёл. Попробуй другое название." if lang == "ru" else "Nothing found. Try another name.", reply_markup=navigation_keyboard(lang=lang, back_callback="workout:menu", back_text="⬅️ Группы" if lang == "ru" else "⬅️ Muscle groups")); return
    title = f"🔎 <b>Результаты для «{text}»</b>\n\nВыбери упражнение:" if lang == "ru" else f"🔎 <b>Results for “{text}”</b>\n\nChoose an exercise:"
    await message.answer(title, parse_mode="HTML", reply_markup=exercise_search_result(items, lang))

async def _show_first_set_prompt(callback: CallbackQuery, state: FSMContext, exercise_name: str, user_id: int) -> None:
    lang = language_code(callback.from_user); previous = await workout_service.latest_set_for_exercise(user_id, exercise_name)
    if previous is not None:
        await state.update_data(previous_weight=previous.weight_kg, previous_reps=previous.reps)
        text = f"🏋️ <b>{exercise_name}</b>\n\nПодход 1\nПоследний раз: {previous.weight_kg:g} кг × {previous.reps}" if lang == "ru" else f"🏋️ <b>{exercise_name}</b>\n\nSet 1\nLast time: {previous.weight_kg:g} kg × {previous.reps}"
        markup = previous_set_keyboard(previous.weight_kg, previous.reps, lang)
    else:
        text = f"🏋️ <b>{exercise_name}</b>\n\nПодход 1\nВес, кг:" if lang == "ru" else f"🏋️ <b>{exercise_name}</b>\n\nSet 1\nWeight, kg:"; markup = navigation_keyboard(lang=lang)
    if callback.message is not None: await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)

async def _start_selected_exercise(callback: CallbackQuery, state: FSMContext, exercise_id: int) -> None:
    lang = language_code(callback.from_user); user_id = await _user_id(callback.from_user.id)
    if user_id is None: await callback.answer("Профиль не найден" if lang == "ru" else "Profile not found", show_alert=True); return
    item = await exercise_catalog.get(exercise_id)
    if item is None: await callback.answer("Упражнение не найдено" if lang == "ru" else "Exercise not found", show_alert=True); return
    data = await state.get_data(); workout_id = data.get("workout_id")
    workout = await workout_service.get_workout_for_user(int(workout_id), user_id) if workout_id else None
    if workout is None:
        category_name = item.muscle_group_ru if lang == "ru" else item.muscle_group_en
        workout = await workout_service.start(user_id=user_id, name=category_name)
    existing = await workout_service.repository.exercises_for_workout(workout.id)
    position = len(existing) + 1
    exercise = await workout_service.add_exercise(workout_id=workout.id, name=item.name_ru if lang == "ru" else item.name_en, position=position)
    await state.update_data(workout_id=workout.id, exercise_id=exercise.id, exercise_name=exercise.name, set_number=1, exercise_position=position, editing_set_id=None, editing_rpe=None)
    await state.set_state(WorkoutStates.weight); await _show_first_set_prompt(callback, state, exercise.name, user_id)

@router.callback_query(F.data.startswith("workout:exercise:"))
async def workout_exercise_selected(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.rsplit(":", 1)[-1]
    if not value.isdigit(): await callback.answer("Некорректное упражнение", show_alert=True); return
    await _start_selected_exercise(callback, state, int(value)); await callback.answer()

@router.callback_query(F.data == "workout:set:repeat")
async def workout_repeat_previous(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user); data = await state.get_data(); weight, reps = data.get("previous_weight"), data.get("previous_reps")
    if weight is None or reps is None: await callback.answer("Предыдущих данных нет" if lang == "ru" else "No previous data", show_alert=True); return
    await state.update_data(weight=float(weight), reps=int(reps)); await state.set_state(WorkoutStates.rpe)
    if callback.message is not None: await callback.message.edit_text("Повторения перенесены. Укажи RPE от 1 до 10 или 0, чтобы пропустить." if lang == "ru" else "Previous weight and reps copied. Enter RPE from 1 to 10, or 0 to skip.", reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()

@router.callback_query(F.data == "workout:set:manual")
async def workout_manual_set(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user); data = await state.get_data(); set_number = int(data.get("set_number", 1)); await state.set_state(WorkoutStates.weight)
    if callback.message is not None: await callback.message.edit_text(f"Подход {set_number}\n\nВес, кг:" if lang == "ru" else f"Set {set_number}\n\nWeight, kg:", reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()

@router.message(WorkoutStates.weight)
async def workout_weight(message: Message, state: FSMContext) -> None:
    lang = language_code(message)
    try: value = float((message.text or "").replace(",", "."))
    except ValueError: await message.answer("Введи вес числом, например 60 или 0." if lang == "ru" else "Enter a weight, for example 60 or 0.", reply_markup=navigation_keyboard(lang=lang)); return
    if value < 0: await message.answer("Вес не может быть отрицательным." if lang == "ru" else "Weight cannot be negative.", reply_markup=navigation_keyboard(lang=lang)); return
    await state.update_data(weight=value); await state.set_state(WorkoutStates.reps); await message.answer("Сколько повторений?" if lang == "ru" else "How many reps?", reply_markup=navigation_keyboard(lang=lang))

@router.message(WorkoutStates.reps)
async def workout_reps(message: Message, state: FSMContext) -> None:
    lang = language_code(message)
    try: reps = int((message.text or "").strip())
    except ValueError: await message.answer("Введи целое число повторений." if lang == "ru" else "Enter a whole number of reps.", reply_markup=navigation_keyboard(lang=lang)); return
    if reps < 1: await message.answer("Повторения должны быть больше нуля." if lang == "ru" else "Reps must be greater than zero.", reply_markup=navigation_keyboard(lang=lang)); return
    await state.update_data(reps=reps); await state.set_state(WorkoutStates.rpe); await message.answer("RPE от 1 до 10? Можно 0, чтобы пропустить." if lang == "ru" else "RPE from 1 to 10? Enter 0 to skip.", reply_markup=navigation_keyboard(lang=lang))

@router.message(WorkoutStates.rpe)
async def workout_rpe(message: Message, state: FSMContext) -> None:
    lang = language_code(message); text = (message.text or "").strip()
    try: rpe = float(text.replace(",", "."))
    except ValueError: await message.answer("Введи RPE от 1 до 10 или 0." if lang == "ru" else "Enter an RPE from 1 to 10 or 0.", reply_markup=navigation_keyboard(lang=lang)); return
    if rpe != 0 and not 1 <= rpe <= 10: await message.answer("RPE должен быть от 1 до 10, либо 0." if lang == "ru" else "RPE must be from 1 to 10, or 0.", reply_markup=navigation_keyboard(lang=lang)); return
    data = await state.get_data(); rpe_value = None if rpe == 0 else rpe
    editing_set_id = data.get("editing_set_id")
    if editing_set_id:
        updated = await workout_service.update_set(set_id=int(editing_set_id), user_id=(await _user_id(message.from_user.id)) or 0, weight_kg=float(data["weight"]), reps=int(data["reps"]), rpe=rpe_value)
        if updated is None:
            await message.answer("Не удалось изменить подход." if lang == "ru" else "Could not update the set.", reply_markup=navigation_keyboard(lang=lang))
            return
        await state.update_data(editing_set_id=None)
        await message.answer("✅ Подход изменён." if lang == "ru" else "✅ Set updated.")
        user_id = await _user_id(message.from_user.id)
        if user_id is not None and data.get("exercise_id"):
            await _render_current_exercise(message, state, int(data["exercise_id"]), user_id)
        return
    await workout_service.add_set(exercise_id=int(data["exercise_id"]), set_number=int(data["set_number"]), weight_kg=float(data["weight"]), reps=int(data["reps"]), rpe=rpe_value)
    next_set = int(data["set_number"]) + 1; await state.update_data(set_number=next_set)
    await message.answer(f"✅ Подход {next_set - 1} записан.\n\nВес следующего подхода, кг:" if lang == "ru" else f"✅ Set {next_set - 1} saved.\n\nWeight for the next set, kg:", reply_markup=workout_set_keyboard(lang))

@router.callback_query(F.data == "workout:set:next")
async def workout_next_set(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    data = await state.get_data()
    if not data.get("exercise_id") or not data.get("workout_id"):
        await callback.answer("Сначала выбери упражнение." if lang == "ru" else "Choose an exercise first.", show_alert=True)
        return
    await state.set_state(WorkoutStates.weight)
    set_number = int(data.get("set_number", 1))
    if callback.message is not None:
        await callback.message.edit_text(f"Подход {set_number}\n\nВес, кг:" if lang == "ru" else f"Set {set_number}\n\nWeight, kg:", reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()

@router.callback_query(F.data == "workout:finish")
async def workout_finish(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user); data = await state.get_data(); user_id = await _user_id(callback.from_user.id)
    workout_id = data.get("workout_id")
    if user_id is None or not workout_id:
        await callback.answer("Активной тренировки нет." if lang == "ru" else "There is no active workout.", show_alert=True)
        return
    workout = await workout_service.get_workout_for_user(int(workout_id), user_id)
    entries = await workout_service.repository.exercises_with_sets_for_workout(int(workout_id)) if workout else []
    total_sets = sum(len(sets) for _, sets in entries)
    if total_sets == 0:
        await callback.answer("Добавь хотя бы один подход перед завершением." if lang == "ru" else "Add at least one set before finishing.", show_alert=True)
        return
    duration_minutes = max(0, int((datetime.now(UTC) - workout.performed_at).total_seconds() // 60)) if workout else 0
    volume = sum(item.weight_kg * item.reps for _, sets in entries for item in sets)
    await workout_service.complete(user_id=user_id, workout_id=int(workout_id), duration_minutes=duration_minutes)
    lines = ["✅ <b>Тренировка завершена</b>" if lang == "ru" else "✅ <b>Workout finished</b>", ""]
    lines.append(f"Упражнений: {len(entries)}" if lang == "ru" else f"Exercises: {len(entries)}")
    for exercise, sets in entries:
        lines.append(f"• {exercise.name} — {len(sets)} " + ("подх." if lang == "ru" else "sets"))
    lines.append(f"Подходов: {total_sets}" if lang == "ru" else f"Sets: {total_sets}")
    lines.append(f"Объём: {volume:g} кг" if lang == "ru" else f"Volume: {volume:g} kg")
    lines.append(f"Время: {duration_minutes} мин" if lang == "ru" else f"Duration: {duration_minutes} min")
    await state.clear()
    if callback.message is not None: await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=dashboard_keyboard(lang))
    await callback.answer()

@router.message(Command("cancel"))
async def workout_cancel(message: Message, state: FSMContext) -> None:
    lang = language_code(message); await state.clear(); await message.answer("Тренировка отменена." if lang == "ru" else "Workout cancelled.", reply_markup=navigation_keyboard(lang=lang))

@router.message(Command("workouts"))
async def workouts(message: Message) -> None:
    lang = language_code(message)
    if message.from_user is None: return
    user_id = await _user_id(message.from_user.id)
    if user_id is None: await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start first."); return
    entries = await workout_service.recent(user_id)
    if not entries: await message.answer("Тренировок пока нет. Открой «Тренировка» с дашборда." if lang == "ru" else "No workouts yet. Open Workout from the dashboard.", reply_markup=navigation_keyboard(lang=lang)); return
    lines = ["🏋️ <b>Последние тренировки</b>" if lang == "ru" else "🏋️ <b>Recent workouts</b>", ""]
    for item in entries: lines.append(f"#{item.id} {item.name} — {item.performed_at.strftime('%d.%m.%Y %H:%M')}")
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))
