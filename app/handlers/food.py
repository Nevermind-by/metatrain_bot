from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import FoodStates
from app.keyboards.food import meal_keyboard
from app.keyboards.navigation import navigation_keyboard
from app.keyboards.product import product_keyboard
from app.repositories.recipe import RecipeRepository
from app.services.food import MEALS, FoodService
from app.services.product import ProductService
from app.services.profile import ProfileService
from app.services.user import UserService

router = Router(name="food")
food_service = FoodService()
profile_service = ProfileService()
product_service = ProductService()
recipe_repository = RecipeRepository()
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
    await message.answer("🍽 <b>Добавить питание</b>\n\nКуда добавить продукт или блюдо?", parse_mode="HTML", reply_markup=meal_keyboard())


@router.message(Command("cancel"))
async def food_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Операция отменена.", reply_markup=navigation_keyboard())


@router.callback_query(FoodStates.meal, F.data.startswith("food:meal:"))
async def food_meal(callback: CallbackQuery, state: FSMContext) -> None:
    meal = callback.data.rsplit(":", 1)[-1]
    if meal not in MEALS:
        await callback.answer("Некорректный приём пищи", show_alert=True)
        return
    user_id = await _user_id(callback.from_user.id)
    if user_id is None:
        await callback.answer("Профиль не найден", show_alert=True)
        return
    await state.update_data(meal=meal)
    products = await product_service.recent(user_id)
    recipes = await recipe_repository.list(user_id)
    await state.set_state(FoodStates.product_name)
    if callback.message is not None:
        if products or recipes:
            await callback.message.edit_text(
                "Выбери сохранённый продукт/блюдо или добавь новый продукт:",
                reply_markup=product_keyboard(products, recipes),
            )
        else:
            await callback.message.edit_text("Название продукта:", reply_markup=navigation_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("food:recipe:"))
async def saved_recipe(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.rsplit(":", 1)[-1]
    if not value.isdigit():
        await callback.answer("Некорректное блюдо", show_alert=True)
        return
    user_id = await _user_id(callback.from_user.id)
    recipe = await recipe_repository.get(user_id, int(value)) if user_id is not None else None
    if recipe is None:
        await callback.answer("Блюдо не найдено", show_alert=True)
        return
    await state.update_data(
        recipe_name=recipe.name,
        calories_per_serving=recipe.calories / recipe.servings,
        protein_per_serving=recipe.protein / recipe.servings,
        fat_per_serving=recipe.fat / recipe.servings,
        carbohydrates_per_serving=recipe.carbohydrates / recipe.servings,
    )
    await state.set_state(FoodStates.recipe)
    if callback.message is not None:
        await callback.message.edit_text(f"{recipe.name}\nСколько порций? Например: 1.5", reply_markup=navigation_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("food:product:"))
async def saved_product(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.rsplit(":", 1)[-1]
    if not value.isdigit():
        await callback.answer("Некорректный продукт", show_alert=True)
        return
    user_id = await _user_id(callback.from_user.id)
    product = await product_service.get(user_id, int(value)) if user_id is not None else None
    if product is None:
        await callback.answer("Продукт не найден", show_alert=True)
        return
    await state.update_data(
        product_name=product.name,
        calories=product.calories,
        protein=product.protein,
        fat=product.fat,
        carbohydrates=product.carbohydrates,
    )
    await state.set_state(FoodStates.grams)
    if callback.message is not None:
        await callback.message.edit_text(f"{product.name}\nСколько граммов? Например: 150", reply_markup=navigation_keyboard())
    await callback.answer()


@router.callback_query(F.data == "food:product:new")
async def new_product_for_food(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FoodStates.product_name)
    if callback.message is not None:
        await callback.message.edit_text("Название продукта:", reply_markup=navigation_keyboard())
    await callback.answer()


@router.message(FoodStates.product_name)
async def food_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Введи название продукта.", reply_markup=navigation_keyboard())
        return
    await state.update_data(product_name=name)
    await state.set_state(FoodStates.grams)
    await message.answer("Сколько граммов? Например: 150", reply_markup=navigation_keyboard())


@router.message(FoodStates.grams)
async def food_grams(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        grams = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 150", reply_markup=navigation_keyboard())
        return
    if grams <= 0:
        await message.answer("Значение должно быть больше нуля.", reply_markup=navigation_keyboard())
        return
    if all(k in data for k in ("calories", "protein", "fat", "carbohydrates")):
        user_id = await _user_id(message.from_user.id) if message.from_user else None
        if user_id is None:
            await state.clear(); await message.answer("Пользователь не найден. Используй /start.", reply_markup=navigation_keyboard()); return
        entry = await food_service.add_product_entry(
            user_id=user_id, meal=data["meal"], product_name=data["product_name"], grams=grams,
            calories_per_100=data["calories"], protein_per_100=data["protein"],
            fat_per_100=data["fat"], carbohydrates_per_100=data["carbohydrates"],
        )
        await state.clear()
        await message.answer(
            f"Добавлено ✅\n{entry.product_name} — {entry.quantity:g} г\n"
            f"{entry.calories:g} ккал • Б {entry.protein:g} г • Ж {entry.fat:g} г • У {entry.carbohydrates:g}",
            reply_markup=navigation_keyboard(),
        )
        return
    await state.update_data(grams=grams)
    await state.set_state(FoodStates.calories)
    await message.answer("Калорийность на 100 г?", reply_markup=navigation_keyboard())


@router.message(FoodStates.recipe)
async def recipe_servings(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        servings = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 1.5", reply_markup=navigation_keyboard())
        return
    if servings <= 0:
        await message.answer("Количество порций должно быть больше нуля.", reply_markup=navigation_keyboard())
        return
    user_id = await _user_id(message.from_user.id) if message.from_user else None
    if user_id is None:
        await state.clear(); await message.answer("Пользователь не найден. Используй /start.", reply_markup=navigation_keyboard()); return
    entry = await food_service.add_recipe_entry(
        user_id=user_id, meal=data["meal"], recipe_name=data["recipe_name"], servings=servings,
        calories_per_serving=data["calories_per_serving"], protein_per_serving=data["protein_per_serving"],
        fat_per_serving=data["fat_per_serving"], carbohydrates_per_serving=data["carbohydrates_per_serving"],
    )
    await state.clear()
    await message.answer(
        f"Добавлено ✅\n🍲 {entry.product_name} — {entry.quantity:g} порц.\n"
        f"{entry.calories:g} ккал • Б {entry.protein:g} г • Ж {entry.fat:g} г • У {entry.carbohydrates:g}",
        reply_markup=navigation_keyboard(),
    )


async def _numeric(message: Message, state: FSMContext, next_state: object, key: str, prompt: str) -> None:
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 12.5", reply_markup=navigation_keyboard())
        return
    if value < 0:
        await message.answer("Значение не может быть отрицательным.", reply_markup=navigation_keyboard())
        return
    await state.update_data(**{key: value})
    await state.set_state(next_state)
    await message.answer(prompt, reply_markup=navigation_keyboard())


@router.message(FoodStates.calories)
async def food_calories(message: Message, state: FSMContext) -> None:
    await _numeric(message, state, FoodStates.protein, "calories", "Белки на 100 г (г)?")


@router.message(FoodStates.protein)
async def food_protein(message: Message, state: FSMContext) -> None:
    await _numeric(message, state, FoodStates.fat, "protein", "Жиры на 100 г (г)?")


@router.message(FoodStates.fat)
async def food_fat(message: Message, state: FSMContext) -> None:
    await _numeric(message, state, FoodStates.carbohydrates, "fat", "Углеводы на 100 г (г)?")


@router.message(FoodStates.carbohydrates)
async def food_carbohydrates(message: Message, state: FSMContext) -> None:
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 20", reply_markup=navigation_keyboard())
        return
    if value < 0:
        await message.answer("Значение не может быть отрицательным.", reply_markup=navigation_keyboard())
        return
    data = await state.get_data()
    await state.update_data(carbohydrates=value)
    await state.set_state(FoodStates.grams)
    await message.answer(f"{data.get('product_name', 'Продукт')}: теперь введи вес в граммах.", reply_markup=navigation_keyboard())


@router.message(Command("today"))
async def today_handler(message: Message) -> None:
    if message.from_user is None: return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start."); return
    entries = await food_service.today(user_id)
    totals = food_service.totals(entries)
    profile = await profile_service.get_profile(user_id)
    if not entries:
        await message.answer("Сегодня пока ничего не записано.", reply_markup=navigation_keyboard()); return
    lines = ["📅 <b>Сегодня</b>", ""]
    for entry in entries:
        lines.append(f"#{entry.id} {MEALS[entry.meal]}: {entry.product_name} — {entry.quantity:g} {entry.unit} ({entry.calories:g} ккал)")
    lines += ["", f"🔥 {totals['calories']:g} ккал", f"🥩 Б {totals['protein']:g} г", f"🥑 Ж {totals['fat']:g} г", f"🍚 У {totals['carbohydrates']:g} г"]
    if profile:
        lines += ["", f"🎯 Цель: {profile.calories} ккал", f"Осталось: {max(0, profile.calories - totals['calories']):g} ккал"]
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=navigation_keyboard())


@router.message(Command("delete_food"))
async def delete_food(message: Message) -> None:
    if message.from_user is None: return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start."); return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используй: /delete_food <id>", reply_markup=navigation_keyboard()); return
    await message.answer("Запись удалена ✅" if await food_service.delete(user_id, int(parts[1])) else "Запись не найдена.", reply_markup=navigation_keyboard())
