from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import RecipeStates
from app.keyboards.recipe import product_picker, recipe_again_keyboard
from app.repositories.product import ProductRepository
from app.services.recipe import RecipeService
from app.services.user import UserService

router = Router(name="recipe")
recipe_service = RecipeService()
product_repository = ProductRepository()
user_service = UserService()


async def _user_id(telegram_id: int) -> int | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    return user.id if user and user.id is not None else None


@router.message(Command("recipe"))
async def recipe_start(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    products = await product_repository.list_recent(user_id, 50)
    if not products:
        await message.answer("Сначала добавь продукты через /product.")
        return
    await state.clear()
    await state.set_state(RecipeStates.name)
    await message.answer("Название блюда?")


@router.message(RecipeStates.name)
async def recipe_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(name=name)
    await state.set_state(RecipeStates.servings)
    await message.answer("Сколько порций получится? Введи целое число.")


@router.message(RecipeStates.servings)
async def recipe_servings(message: Message, state: FSMContext) -> None:
    try:
        servings = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введи целое число порций.")
        return
    if servings < 1:
        await message.answer("Порций должно быть больше нуля.")
        return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await state.clear(); await message.answer("Пользователь не найден. Используй /start."); return
    products = await product_repository.list_recent(user_id, 50)
    await state.update_data(servings=servings, items=[])
    await state.set_state(RecipeStates.product)
    await message.answer("Выбери продукт для блюда:", reply_markup=product_picker(products))


@router.callback_query(RecipeStates.product, F.data.startswith("recipe:product:"))
async def recipe_product(callback: CallbackQuery, state: FSMContext) -> None:
    product_id_text = callback.data.rsplit(":", 1)[-1]
    if not product_id_text.isdigit():
        await callback.answer("Некорректный продукт", show_alert=True); return
    await state.update_data(selected_product=int(product_id_text))
    await state.set_state(RecipeStates.grams)
    if callback.message is not None:
        await callback.message.edit_text("Сколько граммов этого продукта?")
    await callback.answer()


@router.message(RecipeStates.grams)
async def recipe_grams(message: Message, state: FSMContext) -> None:
    try:
        grams = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи вес числом, например 250."); return
    if grams <= 0:
        await message.answer("Вес должен быть больше нуля."); return
    data = await state.get_data()
    items = list(data.get("items", []))
    items.append((data["selected_product"], grams))
    await state.update_data(items=items)
    user_id = await _user_id(message.from_user.id)
    products = await product_repository.list_recent(user_id, 50) if user_id is not None else []
    await state.set_state(RecipeStates.product)
    await message.answer("Продукт добавлен. Выбери следующий или нажми «Готово».", reply_markup=product_picker(products))


@router.callback_query(RecipeStates.product, F.data == "recipe:done")
async def recipe_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    items = data.get("items", [])
    if not items:
        await callback.answer("Добавь хотя бы один продукт", show_alert=True); return
    try:
        recipe = await recipe_service.create(callback.from_user.id, data["name"], data["servings"], items)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True); return
    per = lambda value: round(value / recipe.servings, 1)
    if callback.message is not None:
        await callback.message.edit_text(
            f"Блюдо сохранено ✅\n\n🍽 <b>{recipe.name}</b>\n{recipe.servings} порций\n\n"
            f"На всё блюдо: {recipe.calories:g} ккал • Б {recipe.protein:g} • Ж {recipe.fat:g} • У {recipe.carbohydrates:g}\n"
            f"На порцию: {per(recipe.calories):g} ккал • Б {per(recipe.protein):g} • Ж {per(recipe.fat):g} • У {per(recipe.carbohydrates):g}",
            parse_mode="HTML",
        )
    await state.clear(); await callback.answer()


@router.callback_query(F.data == "recipe:cancel")
async def recipe_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message is not None: await callback.message.edit_text("Создание блюда отменено.")
    await callback.answer()


@router.message(Command("recipes"))
async def recipes_list(message: Message) -> None:
    if message.from_user is None: return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start."); return
    recipes = await recipe_service.list(user_id)
    if not recipes:
        await message.answer("Блюд пока нет. Используй /recipe."); return
    lines = ["🍲 <b>Мои блюда</b>", ""]
    for recipe in recipes:
        lines.append(f"#{recipe.id} {recipe.name} — {recipe.calories / recipe.servings:.0f} ккал/порция")
    await message.answer("\n".join(lines), parse_mode="HTML")
