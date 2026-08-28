from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import FoodStates
from app.i18n import language_code
from app.keyboards.food_flow import meal_keyboard
from app.keyboards.navigation import navigation_keyboard
from app.keyboards.product import catalog_keyboard, catalog_start_keyboard, product_keyboard
from app.repositories.recipe import RecipeRepository
from app.services.food import MEALS, FoodService
from app.services.food_catalog import FoodCatalogService
from app.services.product import ProductService
from app.services.profile import ProfileService
from app.services.user import UserService

router = Router(name="food")
food_service = FoodService()
food_catalog_service = FoodCatalogService()
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
    lang = language_code(message.from_user)
    if await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start.")
        return
    await state.clear()
    await state.set_state(FoodStates.meal)
    text = "🍽 <b>Добавить питание</b>\n\nКуда добавить продукт или блюдо?" if lang == "ru" else "🍽 <b>Add nutrition</b>\n\nWhere should we add the food or dish?"
    await message.answer(text, parse_mode="HTML", reply_markup=meal_keyboard(lang))


@router.message(Command("cancel"))
async def food_cancel(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    await state.clear()
    await message.answer("Операция отменена." if lang == "ru" else "Operation cancelled.", reply_markup=navigation_keyboard(lang=lang))


@router.callback_query(FoodStates.meal, F.data.startswith("food:meal:"))
async def food_meal(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    meal = callback.data.rsplit(":", 1)[-1]
    if meal not in MEALS:
        await callback.answer("Некорректный приём пищи" if lang == "ru" else "Invalid meal", show_alert=True)
        return
    user_id = await _user_id(callback.from_user.id)
    if user_id is None:
        await callback.answer("Профиль не найден" if lang == "ru" else "Profile not found", show_alert=True)
        return
    await state.update_data(meal=meal)
    products = await product_service.recent(user_id)
    recipes = await recipe_repository.list(user_id)
    await state.set_state(FoodStates.product_name)
    if callback.message is not None:
        if products or recipes:
            text = ("🔎 <b>Что съел?</b>\n\nВыбери сохранённое блюдо или продукт либо найди продукт в каталоге:" if lang == "ru" else
                    "🔎 <b>What did you eat?</b>\n\nChoose a saved dish or food, or find a food in the catalog:")
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=product_keyboard(products, recipes, lang))
        else:
            text = ("🔎 <b>Что съел?</b>\n\nНайди продукт в каталоге — например, «курица», «рис» или «творог 5%»." if lang == "ru" else
                    "🔎 <b>What did you eat?</b>\n\nFind a food in the catalog — for example, “chicken”, “rice”, or “cottage cheese”.")
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=catalog_start_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "food:catalog:search")
async def catalog_search_start(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    await state.set_state(FoodStates.product_name)
    text = ("🔎 <b>Поиск продукта</b>\n\nНапиши название продукта, например:\n• курица\n• куриная грудка\n• рис\n• творог 5%" if lang == "ru" else
            "🔎 <b>Find a food</b>\n\nEnter a food name, for example:\n• chicken\n• chicken breast\n• rice\n• cottage cheese")
    if callback.message is not None:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang, back_callback="dashboard:food", back_text="⬅️ Приём пищи" if lang == "ru" else "⬅️ Meal"))
    await callback.answer()


@router.callback_query(F.data.startswith("food:catalog:"))
async def catalog_product_selected(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    value = callback.data.rsplit(":", 1)[-1]
    if not value.isdigit():
        await callback.answer("Некорректный продукт" if lang == "ru" else "Invalid food", show_alert=True)
        return
    item = await food_catalog_service.get(int(value))
    if item is None:
        await callback.answer("Продукт не найден" if lang == "ru" else "Food not found", show_alert=True)
        return

    await state.update_data(
        product_name=item.name,
        catalog_food_id=item.id,
        calories=item.calories_per_100g,
        protein=item.protein_per_100g,
        fat=item.fat_per_100g,
        carbohydrates=item.carbohydrates_per_100g,
    )
    await state.set_state(FoodStates.grams)

    preparation = f" · {item.preparation}" if item.preparation else ""
    brand = f" · {item.brand}" if item.brand else ""
    if lang == "ru":
        text = (f"🍽 <b>{item.name}</b>{preparation}{brand}\n\n"
                f"На 100 г: {item.calories_per_100g:g} ккал · Б {item.protein_per_100g:g} г · Ж {item.fat_per_100g:g} г · У {item.carbohydrates_per_100g:g}\n\n"
                "Сколько граммов?")
        back_text = "⬅️ Новый поиск"
    else:
        text = (f"🍽 <b>{item.name}</b>{preparation}{brand}\n\n"
                f"Per 100 g: {item.calories_per_100g:g} kcal · P {item.protein_per_100g:g} g · F {item.fat_per_100g:g} g · C {item.carbohydrates_per_100g:g}\n\n"
                "How many grams?")
        back_text = "⬅️ New search"
    if callback.message is not None:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang, back_callback="food:catalog:search", back_text=back_text))
    await callback.answer()


@router.message(FoodStates.product_name)
async def food_name(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    name = (message.text or "").strip()
    if not name:
        await message.answer("Введи название продукта." if lang == "ru" else "Enter a food name.", reply_markup=navigation_keyboard(lang=lang))
        return

    items = await food_catalog_service.search(name, limit=12)
    if not items:
        text = ("Ничего не нашёл. Попробуй более простое название, например «курица» или «рис»." if lang == "ru" else
                "Nothing found. Try a simpler name, for example “chicken” or “rice”.")
        await message.answer(text, reply_markup=catalog_start_keyboard(lang))
        return

    text = (f"🔎 <b>Результаты для «{name}»</b>\n\nВыбери подходящий продукт:" if lang == "ru" else
            f"🔎 <b>Results for “{name}”</b>\n\nChoose a food:")
    await message.answer(text, parse_mode="HTML", reply_markup=catalog_keyboard(items, lang))


@router.callback_query(F.data.startswith("food:recipe:"))
async def saved_recipe(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    value = callback.data.rsplit(":", 1)[-1]
    if not value.isdigit():
        await callback.answer("Некорректное блюдо" if lang == "ru" else "Invalid dish", show_alert=True)
        return
    user_id = await _user_id(callback.from_user.id)
    recipe = await recipe_repository.get(user_id, int(value)) if user_id is not None else None
    if recipe is None:
        await callback.answer("Блюдо не найдено" if lang == "ru" else "Dish not found", show_alert=True)
        return
    await state.update_data(recipe_name=recipe.name, calories_per_serving=recipe.calories / recipe.servings, protein_per_serving=recipe.protein / recipe.servings, fat_per_serving=recipe.fat / recipe.servings, carbohydrates_per_serving=recipe.carbohydrates / recipe.servings)
    await state.set_state(FoodStates.recipe)
    text = f"{recipe.name}\nСколько порций? Например: 1.5" if lang == "ru" else f"{recipe.name}\nHow many servings? For example: 1.5"
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()


@router.callback_query(F.data.startswith("food:product:"))
async def saved_product(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    value = callback.data.rsplit(":", 1)[-1]
    if not value.isdigit():
        await callback.answer("Некорректный продукт" if lang == "ru" else "Invalid food", show_alert=True)
        return
    user_id = await _user_id(callback.from_user.id)
    product = await product_service.get(user_id, int(value)) if user_id is not None else None
    if product is None:
        await callback.answer("Продукт не найден" if lang == "ru" else "Food not found", show_alert=True)
        return
    await state.update_data(product_name=product.name, calories=product.calories, protein=product.protein, fat=product.fat, carbohydrates=product.carbohydrates)
    await state.set_state(FoodStates.grams)
    text = f"{product.name}\nСколько граммов? Например: 150" if lang == "ru" else f"{product.name}\nHow many grams? For example: 150"
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()


@router.callback_query(F.data == "food:product:new")
async def new_product_for_food(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_code(callback.from_user)
    await state.set_state(FoodStates.product_name)
    text = "🔎 Найди продукт в каталоге — напиши его название:" if lang == "ru" else "🔎 Find a food in the catalog — enter its name:"
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()


@router.message(FoodStates.grams)
async def food_grams(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    data = await state.get_data()
    try:
        grams = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 150" if lang == "ru" else "Enter a number, for example: 150", reply_markup=navigation_keyboard(lang=lang))
        return
    if grams <= 0:
        await message.answer("Значение должно быть больше нуля." if lang == "ru" else "The value must be greater than zero.", reply_markup=navigation_keyboard(lang=lang))
        return
    if all(k in data for k in ("calories", "protein", "fat", "carbohydrates")):
        user_id = await _user_id(message.from_user.id) if message.from_user else None
        if user_id is None:
            await state.clear()
            await message.answer("Пользователь не найден. Используй /start." if lang == "ru" else "User not found. Use /start.", reply_markup=navigation_keyboard(lang=lang))
            return
        entry = await food_service.add_product_entry(user_id=user_id, meal=data["meal"], product_name=data["product_name"], grams=grams, calories_per_100=data["calories"], protein_per_100=data["protein"], fat_per_100=data["fat"], carbohydrates_per_100=data["carbohydrates"])
        await state.clear()
        if lang == "ru":
            text = f"Добавлено ✅\n{entry.product_name} — {entry.quantity:g} г\n{entry.calories:g} ккал • Б {entry.protein:g} г • Ж {entry.fat:g} г • У {entry.carbohydrates:g}"
        else:
            text = f"Added ✅\n{entry.product_name} — {entry.quantity:g} g\n{entry.calories:g} kcal • P {entry.protein:g} g • F {entry.fat:g} g • C {entry.carbohydrates:g}"
        await message.answer(text, reply_markup=navigation_keyboard(lang=lang))
        return
    await state.update_data(grams=grams)
    await state.set_state(FoodStates.calories)
    await message.answer("Калорийность на 100 г?" if lang == "ru" else "Calories per 100 g?", reply_markup=navigation_keyboard(lang=lang))


@router.message(FoodStates.recipe)
async def recipe_servings(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    data = await state.get_data()
    try:
        servings = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 1.5" if lang == "ru" else "Enter a number, for example: 1.5", reply_markup=navigation_keyboard(lang=lang))
        return
    if servings <= 0:
        await message.answer("Количество порций должно быть больше нуля." if lang == "ru" else "Servings must be greater than zero.", reply_markup=navigation_keyboard(lang=lang))
        return
    user_id = await _user_id(message.from_user.id) if message.from_user else None
    if user_id is None:
        await state.clear()
        await message.answer("Пользователь не найден. Используй /start." if lang == "ru" else "User not found. Use /start.", reply_markup=navigation_keyboard(lang=lang))
        return
    entry = await food_service.add_recipe_entry(user_id=user_id, meal=data["meal"], recipe_name=data["recipe_name"], servings=servings, calories_per_serving=data["calories_per_serving"], protein_per_serving=data["protein_per_serving"], fat_per_serving=data["fat_per_serving"], carbohydrates_per_serving=data["carbohydrates_per_serving"])
    await state.clear()
    if lang == "ru":
        text = f"Добавлено ✅\n🍲 {entry.product_name} — {entry.quantity:g} порц.\n{entry.calories:g} ккал • Б {entry.protein:g} г • Ж {entry.fat:g} г • У {entry.carbohydrates:g}"
    else:
        text = f"Added ✅\n🍲 {entry.product_name} — {entry.quantity:g} servings\n{entry.calories:g} kcal • P {entry.protein:g} g • F {entry.fat:g} g • C {entry.carbohydrates:g}"
    await message.answer(text, reply_markup=navigation_keyboard(lang=lang))


async def _numeric(message: Message, state: FSMContext, next_state: object, key: str, prompt: str) -> None:
    lang = language_code(message.from_user)
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 12.5" if lang == "ru" else "Enter a number, for example: 12.5", reply_markup=navigation_keyboard(lang=lang))
        return
    if value < 0:
        await message.answer("Значение не может быть отрицательным." if lang == "ru" else "The value cannot be negative.", reply_markup=navigation_keyboard(lang=lang))
        return
    await state.update_data(**{key: value})
    await state.set_state(next_state)
    await message.answer(prompt, reply_markup=navigation_keyboard(lang=lang))


@router.message(FoodStates.calories)
async def food_calories(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    await _numeric(message, state, FoodStates.protein, "calories", "Белки на 100 г (г)?" if lang == "ru" else "Protein per 100 g (g)?")


@router.message(FoodStates.protein)
async def food_protein(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    await _numeric(message, state, FoodStates.fat, "protein", "Жиры на 100 г (г)?" if lang == "ru" else "Fat per 100 g (g)?")


@router.message(FoodStates.fat)
async def food_fat(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    await _numeric(message, state, FoodStates.carbohydrates, "fat", "Углеводы на 100 г (г)?" if lang == "ru" else "Carbohydrates per 100 g (g)?")


@router.message(FoodStates.carbohydrates)
async def food_carbohydrates(message: Message, state: FSMContext) -> None:
    lang = language_code(message.from_user)
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 20" if lang == "ru" else "Enter a number, for example: 20", reply_markup=navigation_keyboard(lang=lang))
        return
    if value < 0:
        await message.answer("Значение не может быть отрицательным." if lang == "ru" else "The value cannot be negative.", reply_markup=navigation_keyboard(lang=lang))
        return
    data = await state.get_data()
    await state.update_data(carbohydrates=value)
    await state.set_state(FoodStates.grams)
    product_name = data.get("product_name", "Продукт" if lang == "ru" else "Food")
    text = f"{product_name}: теперь введи вес в граммах." if lang == "ru" else f"{product_name}: now enter the weight in grams."
    await message.answer(text, reply_markup=navigation_keyboard(lang=lang))


@router.message(Command("today"))
async def today_handler(message: Message) -> None:
    lang = language_code(message.from_user)
    if message.from_user is None:
        return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start.")
        return
    entries = await food_service.today(user_id)
    totals = food_service.totals(entries)
    profile = await profile_service.get_profile(user_id)
    if not entries:
        await message.answer("Сегодня пока ничего не записано." if lang == "ru" else "Nothing logged today yet.", reply_markup=navigation_keyboard(lang=lang))
        return
    lines = ["📅 <b>Сегодня</b>" if lang == "ru" else "📅 <b>Today</b>", ""]
    for entry in entries:
        meal = MEALS[entry.meal]
        lines.append(f"#{entry.id} {meal}: {entry.product_name} — {entry.quantity:g} {entry.unit} ({entry.calories:g} {'ккал' if lang == 'ru' else 'kcal'})")
    if lang == "ru":
        lines += ["", f"🔥 {totals['calories']:g} ккал", f"🥩 Б {totals['protein']:g} г", f"🥑 Ж {totals['fat']:g} г", f"🍚 У {totals['carbohydrates']:g} г"]
        if profile:
            lines += ["", f"🎯 Цель: {profile.calories} ккал", f"Осталось: {max(0, profile.calories - totals['calories']):g} ккал"]
    else:
        lines += ["", f"🔥 {totals['calories']:g} kcal", f"🥩 P {totals['protein']:g} g", f"🥑 F {totals['fat']:g} g", f"🍚 C {totals['carbohydrates']:g} g"]
        if profile:
            lines += ["", f"🎯 Target: {profile.calories} kcal", f"Remaining: {max(0, profile.calories - totals['calories']):g} kcal"]
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))


@router.message(Command("delete_food"))
async def delete_food(message: Message) -> None:
    lang = language_code(message.from_user)
    if message.from_user is None:
        return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start." if lang == "ru" else "Create your profile with /start.")
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используй: /delete_food <id>" if lang == "ru" else "Use: /delete_food <id>", reply_markup=navigation_keyboard(lang=lang))
        return
    deleted = await food_service.delete(user_id, int(parts[1]))
    await message.answer(("Запись удалена ✅" if deleted else "Запись не найдена.") if lang == "ru" else ("Entry deleted ✅" if deleted else "Entry not found."), reply_markup=navigation_keyboard(lang=lang))
