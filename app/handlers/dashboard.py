from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import ProgressStates, WeightStates, WorkoutStates
from app.keyboards.dashboard import dashboard_keyboard
from app.services.dashboard import DashboardService
from app.services.user import UserService

router = Router(name="dashboard")
dashboard_service = DashboardService()
user_service = UserService()


async def _render(target: Message | CallbackQuery, user_id: int) -> None:
    text = await dashboard_service.build(user_id)
    if isinstance(target, CallbackQuery):
        if target.message is not None:
            await target.message.edit_text(text, parse_mode="HTML", reply_markup=dashboard_keyboard())
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=dashboard_keyboard())


@router.message(Command("dashboard", "stats"))
async def dashboard_handler(message: Message) -> None:
    if message.from_user is None: return
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None or user.id is None:
        await message.answer("Сначала создай профиль через /start."); return
    await _render(message, user.id)


@router.callback_query(F.data == "dashboard:refresh")
async def dashboard_refresh(callback: CallbackQuery) -> None:
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None or user.id is None:
        await callback.answer("Сначала создай профиль", show_alert=True); return
    await _render(callback, user.id)
    await callback.answer("Обновлено")


@router.callback_query(F.data.in_({"dashboard:food", "dashboard:workout", "dashboard:weight", "dashboard:progress", "dashboard:profile"}))
async def dashboard_action(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.rsplit(":", 1)[-1]
    await state.clear()
    if action == "food":
        from app.handlers.food import food_start
        if callback.message is not None:
            await callback.message.answer("Используй /food для добавления еды.")
    elif action == "workout":
        await state.set_state(WorkoutStates.name)
        if callback.message is not None: await callback.message.answer("Название тренировки? Например: Грудь + трицепс")
    elif action == "weight":
        await state.set_state(WeightStates.value)
        if callback.message is not None: await callback.message.answer("Введи текущий вес в кг, например: 82.4")
    elif action == "progress":
        await state.set_state(ProgressStates.exercise)
        if callback.message is not None: await callback.message.answer("Какое упражнение показать? Например: Жим лёжа")
    elif action == "profile":
        if callback.message is not None: await callback.message.answer("Открой профиль: /profile")
    await callback.answer()


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "<b>MetaTrain</b>\n\n"
        "/start — профиль\n"
        "/profile — профиль и настройки\n"
        "/food — добавить еду\n"
        "/today — питание за сегодня\n"
        "/weight — записать вес\n"
        "/weights — история веса\n"
        "/workout — записать тренировку\n"
        "/workouts — история тренировок\n"
        "/progress — прогресс упражнения\n"
        "/dashboard — сводка\n"
        "/cancel — отменить текущий ввод",
        parse_mode="HTML",
    )
