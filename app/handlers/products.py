from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states import ProductStates
from app.services.product import ProductService
from app.services.user import UserService

router = Router(name="products")
product_service = ProductService()
user_service = UserService()


async def _user_id(telegram_id: int) -> int | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    return user.id if user and user.id is not None else None


@router.message(Command("product"))
async def product_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    if message.from_user is None or await _user_id(message.from_user.id) is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    await state.set_state(ProductStates.name)
    await message.answer("Название продукта?\n\n/cancel — отменить")


@router.message(ProductStates.name)
async def product_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Введи название продукта.")
        return
    await state.update_data(name=name)
    await state.set_state(ProductStates.calories)
    await message.answer("Ккал на 100 г?")


async def _number(message: Message, state: FSMContext, key: str, next_state, prompt: str) -> None:
    try:
        value = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число.")
        return
    if value < 0:
        await message.answer("Значение не может быть отрицательным.")
        return
    await state.update_data(**{key: value})
    await state.set_state(next_state)
    await message.answer(prompt)


@router.message(ProductStates.calories)
async def product_calories(message: Message, state: FSMContext) -> None:
    await _number(message, state, "calories", ProductStates.protein, "Белки на 100 г?")


@router.message(ProductStates.protein)
async def product_protein(message: Message, state: FSMContext) -> None:
    await _number(message, state, "protein", ProductStates.fat, "Жиры на 100 г?")


@router.message(ProductStates.fat)
async def product_fat(message: Message, state: FSMContext) -> None:
    await _number(message, state, "fat", ProductStates.carbohydrates, "Углеводы на 100 г?")


@router.message(ProductStates.carbohydrates)
async def product_carbohydrates(message: Message, state: FSMContext) -> None:
    try:
        carbohydrates = float((message.text or "").replace(",", "."))
    except ValueError:
        await message.answer("Введи число.")
        return
    if carbohydrates < 0:
        await message.answer("Значение не может быть отрицательным.")
    else:
        data = await state.get_data()
        user_id = await _user_id(message.from_user.id)
        if user_id is not None:
            try:
                product = await product_service.create(
                    user_id=user_id, name=data["name"], calories=data["calories"],
                    protein=data["protein"], fat=data["fat"], carbohydrates=carbohydrates,
                )
                await message.answer(f"Продукт сохранён ✅\n{product.name}\n{product.calories:g} ккал • Б {product.protein:g} • Ж {product.fat:g} • У {product.carbohydrates:g}\n\nТеперь его можно использовать как сохранённый продукт.")
            except ValueError as exc:
                await message.answer(str(exc))
        await state.clear()


@router.message(Command("products"))
async def products_list(message: Message) -> None:
    if message.from_user is None:
        return
    user_id = await _user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Сначала создай профиль через /start.")
        return
    products = await product_service.recent(user_id)
    if not products:
        await message.answer("Каталог пуст. Используй /product, чтобы добавить продукт.")
        return
    lines = ["📦 <b>Мои продукты</b>", ""]
    for product in products:
        lines.append(f"#{product.id} {product.name} — {product.calories:g} ккал | Б {product.protein:g} | Ж {product.fat:g} | У {product.carbohydrates:g}")
    await message.answer("\n".join(lines), parse_mode="HTML")
