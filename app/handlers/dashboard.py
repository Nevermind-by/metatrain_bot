from collections import defaultdict
from datetime import datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import FoodStates, ProgressStates, WeightStates, WorkoutStates
from app.i18n import language_code
from app.keyboards.dashboard import dashboard_keyboard
from app.keyboards.food_flow import meal_keyboard
from app.keyboards.navigation import navigation_keyboard
from app.services.dashboard import DashboardService
from app.services.food import MEALS, FoodService
from app.services.profile import ProfileService
from app.services.user import UserService
from app.services.workout import WorkoutService

router = Router(name="dashboard")
dashboard_service = DashboardService(); food_service = FoodService(); profile_service = ProfileService(); user_service = UserService(); workout_service = WorkoutService()


async def _user(target: Message | CallbackQuery):
    user = await user_service.get_by_telegram_id(target.from_user.id)
    if user is None or user.id is None: return None
    return user


async def _render(target: Message | CallbackQuery, user_id: int) -> bool:
    text = await dashboard_service.build(user_id)
    lang = language_code(target.from_user)
    markup = dashboard_keyboard(lang)
    if isinstance(target, CallbackQuery):
        if target.message is not None:
            try:
                await target.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
            except TelegramBadRequest as exc:
                if "message is not modified" not in str(exc).lower(): raise
                return False
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=markup)
    return True


@router.message(Command("dashboard", "stats"))
async def dashboard_handler(message: Message) -> None:
    user = await _user(message); lang = language_code(message.from_user)
    if user is None:
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start first."); return
    await _render(message, user.id)


@router.callback_query(F.data == "dashboard:home")
async def dashboard_home(callback: CallbackQuery, state: FSMContext) -> None:
    user = await _user(callback); lang = language_code(callback.from_user)
    if user is None:
        await callback.answer("Сначала создай профиль" if lang == "ru" else "Create your profile first", show_alert=True); return
    await state.clear(); await _render(callback, user.id); await callback.answer()


@router.callback_query(F.data == "dashboard:refresh")
async def dashboard_refresh(callback: CallbackQuery) -> None:
    user = await _user(callback)
    if user is None:
        await callback.answer("Сначала создай профиль" if language_code(callback.from_user) == "ru" else "Create your profile first", show_alert=True); return
    updated = await _render(callback, user.id)
    await callback.answer(("Обновлено" if updated else "Всё актуально") if language_code(callback.from_user) == "ru" else ("Updated" if updated else "Already up to date"))


@router.callback_query(F.data == "dashboard:food")
async def dashboard_food(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear(); await state.set_state(FoodStates.meal)
    lang = language_code(callback.from_user)
    if callback.message is not None:
        await callback.message.edit_text("🍽 <b>Питание</b>\n\nВыбери действие:" if lang == "ru" else "🍽 <b>Nutrition</b>\n\nChoose an action:", parse_mode="HTML", reply_markup=meal_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "dashboard:today")
async def dashboard_today(callback: CallbackQuery) -> None:
    user = await _user(callback); lang = language_code(callback.from_user)
    if user is None:
        await callback.answer("Сначала создай профиль" if lang == "ru" else "Create your profile first", show_alert=True); return
    entries = await food_service.today(user.id)
    if not entries:
        text = "📅 <b>Питание сегодня</b>\n\nПока ничего не записано." if lang == "ru" else "📅 <b>Today's nutrition</b>\n\nNothing logged yet."
    else:
        totals = food_service.totals(entries); lines = ["📅 <b>Питание сегодня</b>" if lang == "ru" else "📅 <b>Today's nutrition</b>", ""]
        for entry in entries:
            meal_name = MEALS[entry.meal]
            lines.append(f"{meal_name} {entry.product_name} — {entry.quantity:g} {entry.unit} ({entry.calories:g} kcal)")
        lines += ["", f"🔥 {totals['calories']:g} kcal", f"🥩 {'Б' if lang == 'ru' else 'P'} {totals['protein']:g} g", f"🥑 {'Ж' if lang == 'ru' else 'F'} {totals['fat']:g} g", f"🍚 {'У' if lang == 'ru' else 'C'} {totals['carbohydrates']:g} g"]
        profile = await profile_service.get_profile(user.id)
        if profile: lines += ["", f"🎯 {'Цель' if lang == 'ru' else 'Target'}: {profile.calories} kcal", f"{'Осталось' if lang == 'ru' else 'Remaining'}: {max(0, profile.calories - totals['calories']):g} kcal"]
        text = "\n".join(lines)
    if callback.message is not None: await callback.message.edit_text(text, parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang, back_callback="dashboard:food"))
    await callback.answer()
