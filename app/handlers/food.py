from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import FoodStates
from app.keyboards.food import meal_keyboard
from app.services.food import FoodService, MEALS
from app.services.profile import ProfileService
from app.services.user import UserService

router = Router(name="food")
food_service = FoodService()
profile_service = ProfileService()
user_service = UserService()


async def _user_id(telegram_id: int) -> int | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    return user.id if user and user.id is not None else None


@router.message(Command("food"))
async def food_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    if await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    await state.clear()
    await state.set_state(FoodStates.meal)
    await message.answer("Куда добавить продукт?", reply_markup=meal_keyboard())


@router.message(Command("cancel"))
async def food_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Операция отменена.")


@router.callback_query(FoodStates.meal, F.data.startswith("food:meal:"))
async def food_meal(callback: CallbackQuery, state: FSMContext) -> None:
    meal = callback.data.rsplit(":", 1)[-1]
    if meal not in MEALS:
        await callback.answer("Некорректный приём пищи", show_alert=True)
        return
    await state.update_data(meal=meal)
    await state.set_state(FoodStates.product_name)
    if callback.message is not None:
        await callback.message.edit_text("Название продукта:\n\n/cancel — отменить")
    await callback.answer()


@router.message(FoodStates.product_name)
async def food_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Введи название продукта.")
        return
    await state.update_data(product_name=name)
    await state.set_state(FoodStates.grams)
    await message.answer("Сколько граммов? Например: 150")


async def _numeric(message: Message, state: FSMContext, next_state: object, key: str, prompt: str, minimum: float) -> None:
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 12.5")
        return
    if value < minimum:
        await message.answer(f"Значение не может быть меньше {minimum}.")
        return
    await state.update_data(**{key: value})
    await state.set_state(next_state)
    await message.answer(prompt)


@router.message(FoodStates.grams)
async def food_grams(message: Message, state: FSMContext) -> None:
    await _numeric(message, state, FoodStates.calories, "grams", "Калорийность на 100 г?", 0.1)


@router.message(FoodStates.calories)
async def food_calories(message: Message, state: FSMContext) -> None:
    await _numeric(message, state, FoodStates.protein, "calories", "Белки на 100 г (г)?", 0)


@router.message(FoodStates.protein)
async def food_protein(message: Message, state: FSMContext) -> None:
    await _numeric(message, state, FoodStates.fat, "protein", "Жиры на 100 г (г)?", 0)


@router.message(FoodStates.fat)
async def food_fat(message: Message, state: FSMContext) -> None:
    await _numeric(message, state, FoodStates.carbohydrates, "fat", "Углеводы на 100 г (г)?", 0)


@router.message(FoodStates.carbohydrates)
async def food_carbohydrates(message: Message, state: FSMContext) -> None:
    try:
        carbohydrates = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 20")
        return
    if carbohydrates < 0:
        await message.answer("Углеводы не могут быть отрицательными.")
        return

    data = await state.get_data()
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await state.clear()
        await message.answer("Пользователь не найден. Используй /start.")
        return

    entry = await food_service.add_entry(
        user_id=user_id,
        meal=data["meal"],
        product_name=data["product_name"],
        grams=data["grams"],
        calories_per_100=data["calories"],
        protein_per_100=data["protein"],
        fat_per_100=data["fat"],
        carbohydrates_per_100=carbohydrates,
    )
    await state.clear()
    await message.answer(
        f"Добавлено ✅\n\n{entry.product_name} — {entry.grams:g} г\n"
        f"{entry.calories:g} ккал • Б {entry.protein:g} г • Ж {entry.fat:g} г • У {entry.carbohydrates:g}\n\n"
        "Смотреть дневник: /today"
    )


@router.message(Command("today"))
async def today_handler(message: Message) -> None:
    if message.from_user is None:
        return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start.")
        return

    entries = await food_service.today(user_id)
    totals = food_service.totals(entries)
    profile = await profile_service.get_profile(user_id)
    if not entries:
        await message.answer("Сегодня пока ничего не записано.")
        return

    lines = ["📅 <b>Сегодня</b>", ""]
    for entry in entries:
        lines.append(f"{MEALS[entry.meal]}: {entry.product_name} — {entry.grams:g} г ({entry.calories:g} ккал)")
    lines.extend([
        "",
        f"🔥 {totals['calories']:g} ккал",
        f"🥩 Б {totals['protein']:g} г",
        f"🥑 Ж {totals['fat']:g} г",
        f"🍚 У {totals['carbohydrates']:g} г",
    ])
    if profile is not None:
        lines.extend([
            "",
            f"🎯 Цель: {profile.calories} ккал",
            f"Осталось: {max(0, profile.calories - totals['calories']):g} ккал",
        ])
    await message.answer("\n".join(lines), parse_mode="HTML")
