from __future__ import annotations

import base64
from io import BytesIO

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (\n    CallbackQuery,\n    InlineKeyboardButton,\n    InlineKeyboardMarkup,\n    Message,\n)

from app.bot.states import SmartFoodStates
from app.config.settings import settings
from app.i18n import language_code
from app.keyboards.navigation import navigation_keyboard
from app.repositories.user import UserRepository
from app.services.food import FoodService
from app.services.food_catalog import FoodCatalogService
from app.services.smart_food import detect_meal, extract_food_with_ai

router = Router(name="smart_food")
catalog = FoodCatalogService()
food_service = FoodService()
users = UserRepository()


def buttons(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Добавить" if lang == "ru" else "✅ Add", callback_data="smart:confirm")],
        [InlineKeyboardButton(text="🔄 Заново" if lang == "ru" else "🔄 Start over", callback_data="smart:restart")],
        [InlineKeyboardButton(text="🏠 Дашборд", callback_data="dashboard:home")],
    ])


def preview(items, lang):
    total = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbohydrates": 0.0}
    lines = ["🍽 <b>Проверь приём пищи</b>", ""] if lang == "ru" else ["🍽 <b>Review meal</b>", ""]
    for item in items:
        calc = item["calc"]
        for key in total:
            total[key] += calc[key]
        lines.append(
            f"• {item['food_name']} — {item['amount']:g} г: {calc['calories']:g} ккал · Б {calc['protein']:g} · Ж {calc['fat']:g} · У {calc['carbohydrates']:g}"
            if lang == "ru" else
            f"• {item['food_name']} — {item['amount']:g} g: {calc['calories']:g} kcal · P {calc['protein']:g} · F {calc['fat']:g} · C {calc['carbohydrates']:g}"
        )
    lines.append("")
    lines.append(
        f"<b>Итого: {total['calories']:g} ккал · Б {total['protein']:g} · Ж {total['fat']:g} · У {total['carbohydrates']:g}</b>"
        if lang == "ru" else
        f"<b>Total: {total['calories']:g} kcal · P {total['protein']:g} · F {total['fat']:g} · C {total['carbohydrates']:g}</b>"
    )
    return "\n".join(lines)


async def process(message: Message, state: FSMContext, text: str, image_url: str | None = None):
    lang = language_code(message.from_user)
    parsed = await extract_food_with_ai(text, image_url)
    if not parsed:
        await message.answer("Не смог разобрать продукты. Напиши список текстом." if lang == "ru" else "I could not parse the foods. Send them as text.", reply_markup=navigation_keyboard(lang=lang))
        return
    meal = detect_meal(text) or (await state.get_data()).get("meal") or "snack"
    if any(item.amount is None for item in parsed):
        names = ", ".join(item.raw_name for item in parsed if item.amount is None)
        await message.answer(f"Не указана граммовка: {names}" if lang == "ru" else f"Missing quantity: {names}")
        return
    resolved = []
    missing = []
    for item in parsed:
        matches = await catalog.search(item.raw_name, limit=5)
        if not matches:
            missing.append(item.raw_name)
            continue
        food = matches[0]
        resolved.append({"food_id": food.id, "food_name": food.name, "amount": float(item.amount), "calc": catalog.calculate(food, float(item.amount))})
    if missing:
        await message.answer(
            ("Не нашёл в каталоге: " + ", ".join(missing) + ". Уточни название и отправь список ещё раз.")
            if lang == "ru" else
            ("Not found in catalog: " + ", ".join(missing) + ". Clarify the names and send the list again."),
            reply_markup=navigation_keyboard(lang=lang),
        )
        return
    await state.update_data(meal=meal, resolved=resolved)
    await state.set_state(SmartFoodStates.confirm)
    await message.answer(preview(resolved, lang), parse_mode="HTML", reply_markup=buttons(lang))


@router.callback_query(F.data == "food:smart:start")
async def smart_start(callback: CallbackQuery, state: FSMContext):
    lang = language_code(callback.from_user)
    current = await state.get_data()
    await state.set_state(SmartFoodStates.input)
    await state.update_data(meal=current.get("meal"))
    text = (
        "🧠 <b>Быстрый ввод питания</b>\n\n"
        "Напиши продукты как удобно. Шаблон не нужен: можно менять порядок, ставить граммы до или после продукта, использовать «г», «гр», «грамм».\n\n"
        "Например:\nРис отварной 150г\nРубленные куриные котлеты 100г\nМасло сливочное 82% 5г\n\n"
        "Можно также отправить фото с подписью."
        if lang == "ru" else
        "🧠 <b>Quick food entry</b>\n\nSend foods naturally; no fixed template is required.\n\nYou can also send a photo with a caption."
    )
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()


@router.message(SmartFoodStates.input, F.photo)
async def smart_photo(message: Message, state: FSMContext):
    if not settings.openai_api_key:
        await message.answer("Для анализа фото добавь OPENAI_API_KEY в настройки Render/.env." if language_code(message.from_user) == "ru" else "Set OPENAI_API_KEY in Render/.env to enable photo analysis.")
        return
    file = await message.bot.get_file(message.photo[-1].file_id)
    buffer = BytesIO()
    await message.bot.download_file(file.file_path, destination=buffer)
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    await process(message, state, message.caption or "", f"data:image/jpeg;base64,{data}")


@router.message(SmartFoodStates.input)
async def smart_text(message: Message, state: FSMContext):
    await process(message, state, message.text or "")


@router.callback_query(SmartFoodStates.confirm, F.data == "smart:confirm")
async def smart_confirm(callback: CallbackQuery, state: FSMContext):
    lang = language_code(callback.from_user)
    data = await state.get_data()
    user = await users.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Пользователь не найден" if lang == "ru" else "User not found", show_alert=True)
        return
    for item in data.get("resolved", []):
        calc = item["calc"]
        amount = item["amount"]
        await food_service.add_product_entry(
            user_id=user.id, meal=data["meal"], product_name=item["food_name"], grams=amount,
            calories_per_100=calc["calories"] * 100 / amount,
            protein_per_100=calc["protein"] * 100 / amount,
            fat_per_100=calc["fat"] * 100 / amount,
            carbohydrates_per_100=calc["carbohydrates"] * 100 / amount,
        )
    await state.clear()
    if callback.message:
        await callback.message.edit_text("Добавлено в дневник ✅" if lang == "ru" else "Added to diary ✅", reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()


@router.callback_query(SmartFoodStates.confirm, F.data == "smart:restart")
async def smart_restart(callback: CallbackQuery, state: FSMContext):
    lang = language_code(callback.from_user)
    await state.set_state(SmartFoodStates.input)
    if callback.message:
        await callback.message.edit_text("Отправь список продуктов заново." if lang == "ru" else "Send the food list again.", reply_markup=navigation_keyboard(lang=lang))
    await callback.answer()
