from collections import defaultdict
from datetime import datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import FoodStates, ProgressStates, WeightStates, WorkoutStates
from app.keyboards.dashboard import dashboard_keyboard
from app.keyboards.food_flow import meal_keyboard
from app.keyboards.navigation import navigation_keyboard
from app.services.dashboard import DashboardService
from app.services.food import MEALS, FoodService
from app.services.profile import ProfileService
from app.services.user import UserService
from app.services.workout import WorkoutService

router = Router(name="dashboard")
dashboard_service = DashboardService()
food_service = FoodService()
profile_service = ProfileService()
user_service = UserService()
workout_service = WorkoutService()


async def _user(target: Message | CallbackQuery):
    user = await user_service.get_by_telegram_id(target.from_user.id)
    if user is None or user.id is None:
        return None
    return user


async def _render(target: Message | CallbackQuery, user_id: int) -> bool:
    text = await dashboard_service.build(user_id)
    if isinstance(target, CallbackQuery):
        if target.message is not None:
            try:
                await target.message.edit_text(
                    text, parse_mode="HTML", reply_markup=dashboard_keyboard()
                )
            except TelegramBadRequest as exc:
                if "message is not modified" not in str(exc).lower():
                    raise
                return False
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=dashboard_keyboard())
    return True


@router.message(Command("dashboard", "stats"))
async def dashboard_handler(message: Message) -> None:
    user = await _user(message)
    if user is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    await _render(message, user.id)


@router.callback_query(F.data == "dashboard:home")
async def dashboard_home(callback: CallbackQuery, state: FSMContext) -> None:
    user = await _user(callback)
    if user is None:
        await callback.answer("Сначала создай профиль", show_alert=True)
        return
    await state.clear()
    await _render(callback, user.id)
    await callback.answer()


@router.callback_query(F.data == "dashboard:refresh")
async def dashboard_refresh(callback: CallbackQuery) -> None:
    user = await _user(callback)
    if user is None:
        await callback.answer("Сначала создай профиль", show_alert=True)
        return
    updated = await _render(callback, user.id)
    await callback.answer("Обновлено" if updated else "Всё актуально")


@router.callback_query(F.data == "dashboard:food")
async def dashboard_food(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(FoodStates.meal)
    if callback.message is not None:
        await callback.message.edit_text(
            "🍽 <b>Питание</b>\n\nВыбери действие:",
            parse_mode="HTML",
            reply_markup=meal_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "dashboard:today")
async def dashboard_today(callback: CallbackQuery) -> None:
    user = await _user(callback)
    if user is None:
        await callback.answer("Сначала создай профиль", show_alert=True)
        return
    entries = await food_service.today(user.id)
    if not entries:
        text = "📅 <b>Питание сегодня</b>\n\nПока ничего не записано."
    else:
        totals = food_service.totals(entries)
        lines = ["📅 <b>Питание сегодня</b>", ""]
        for entry in entries:
            lines.append(f"{MEALS[entry.meal]} {entry.product_name} — {entry.quantity:g} {entry.unit} ({entry.calories:g} ккал)")
        lines += [
            "",
            f"🔥 {totals['calories']:g} ккал",
            f"🥩 Б {totals['protein']:g} г • 🥑 Ж {totals['fat']:g} г • 🍚 У {totals['carbohydrates']:g} г",
        ]
        text = "\n".join(lines)
    if callback.message is not None:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=navigation_keyboard())
    await callback.answer()


@router.callback_query(F.data == "dashboard:history")
async def dashboard_history(callback: CallbackQuery) -> None:
    user = await _user(callback)
    if user is None:
        await callback.answer("Сначала создай профиль", show_alert=True)
        return
    entries = await food_service.history(user.id, 7)
    if not entries:
        text = "📚 <b>История питания</b>\n\nЗа последние 7 дней записей нет."
    else:
        daily = defaultdict(list)
        for entry in entries:
            daily[entry.eaten_at.date().isoformat()].append(entry)
        lines = ["📚 <b>История питания · 7 дней</b>", ""]
        for day in sorted(daily, reverse=True):
            total = food_service.totals(daily[day])
            label = datetime.fromisoformat(day).strftime("%d.%m")
            lines.append(f"<b>{label}</b> — {total['calories']:g} ккал • Б {total['protein']:g} • Ж {total['fat']:g} • У {total['carbohydrates']:g}")
        lines += ["", f"Среднее: {food_service.average_daily_calories(entries, 7):g} ккал/день"]
        text = "\n".join(lines)
    if callback.message is not None:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=navigation_keyboard())
    await callback.answer()


@router.callback_query(F.data == "dashboard:workout")
async def dashboard_workout(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(WorkoutStates.name)
    if callback.message is not None:
        await callback.message.edit_text(
            "🏋️ <b>Новая тренировка</b>\n\nНазвание тренировки?\nНапример: Грудь + трицепс",
            parse_mode="HTML",
            reply_markup=navigation_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "dashboard:workouts")
async def dashboard_workouts(callback: CallbackQuery) -> None:
    user = await _user(callback)
    if user is None:
        await callback.answer("Сначала создай профиль", show_alert=True)
        return
    entries = await workout_service.recent(user.id)
    if not entries:
        text = "🏋️ <b>История тренировок</b>\n\nТренировок пока нет."
    else:
        lines = ["🏋️ <b>История тренировок</b>", ""]
        for item in entries:
            lines.append(f"#{item.id} {item.name} — {item.performed_at.strftime('%d.%m.%Y %H:%M')}")
        text = "\n".join(lines)
    if callback.message is not None:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=navigation_keyboard())
    await callback.answer()


@router.callback_query(F.data == "dashboard:weight")
async def dashboard_weight(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(WeightStates.value)
    if callback.message is not None:
        await callback.message.edit_text(
            "⚖️ <b>Записать вес</b>\n\nВведи текущий вес в кг, например: 82.4",
            parse_mode="HTML",
            reply_markup=navigation_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "dashboard:progress")
async def dashboard_progress(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProgressStates.exercise)
    if callback.message is not None:
        await callback.message.edit_text(
            "📈 <b>Прогресс упражнения</b>\n\nКакое упражнение показать?\nНапример: Жим лёжа",
            parse_mode="HTML",
            reply_markup=navigation_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "dashboard:profile")
async def dashboard_profile(callback: CallbackQuery) -> None:
    user = await _user(callback)
    if user is None:
        await callback.answer("Сначала создай профиль", show_alert=True)
        return
    profile = await profile_service.get_profile(user.id)
    if callback.message is not None and profile is not None:
        from app.keyboards.profile_view import profile_keyboard
        await callback.message.edit_text(
            profile_service.format_profile(profile),
            parse_mode="HTML",
            reply_markup=profile_keyboard(),
        )
    await callback.answer()


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    user = await _user(message)
    if user is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    await _render(message, user.id)
