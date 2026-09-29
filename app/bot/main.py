import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, Update
from fastapi import FastAPI, Header, HTTPException, Request, Response

from app.config.settings import settings
from app.database.connection import init_database
from app.handlers.dashboard import router as dashboard_router
from app.handlers.food import router as food_router
from app.handlers.history import router as history_router
from app.handlers.main_menu import router as main_menu_router
from app.handlers.products import router as products_router
from app.handlers.profile import router as profile_router
from app.handlers.progress import router as progress_router
from app.handlers.recipe import router as recipe_router
from app.handlers.smart_food import router as smart_food_router
from app.handlers.start import router as start_router
from app.handlers.webapp import router as webapp_router
from app.handlers.workout import router as workout_router

logger = logging.getLogger(__name__)

BOT_NAME = "MetaTrain | Fitness & Nutrition"
BOT_SHORT_DESCRIPTION = "Питание, тренировки и прогресс - в одном месте."
BOT_DESCRIPTION = (
    "MetaTrain - твой помощник по питанию, тренировкам и прогрессу.\n\n"
    "Настрой профиль, получи персональную дневную норму, веди питание и тренировки, "
    "контролируй вес и следи за результатами.\n\n"
    "Всё управление - через понятный дашборд внутри Telegram."
)

BOT_COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="profile", description="Профиль и настройки"),
    BotCommand(command="food", description="Добавить питание"),
    BotCommand(command="today", description="Питание за сегодня"),
    BotCommand(command="weight", description="Записать вес"),
    BotCommand(command="weights", description="История веса"),
    BotCommand(command="workout", description="Записать тренировку"),
    BotCommand(command="workouts", description="История тренировок"),
    BotCommand(command="progress", description="Прогресс упражнения"),
    BotCommand(command="dashboard", description="Общая сводка"),
    BotCommand(command="webapp", description="Открыть Web App"),
    BotCommand(command="help", description="Все возможности"),
]

WEBHOOK_PATH = "/telegram/webhook"

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dispatcher = Dispatcher()

for router in (
    start_router,
    workout_router,
    main_menu_router,
    webapp_router,
    profile_router,
    food_router,
    smart_food_router,
    products_router,
    recipe_router,
    progress_router,
    dashboard_router,
    history_router,
):
    dispatcher.include_router(router)


async def configure_bot(*, webhook: bool) -> None:
    await bot.set_my_name(BOT_NAME)
    await bot.set_my_short_description(BOT_SHORT_DESCRIPTION)
    await bot.set_my_description(BOT_DESCRIPTION)
    await bot.set_my_commands(BOT_COMMANDS)
    await init_database()

    if webhook:
        if not settings.render_external_url:
            raise RuntimeError("RENDER_EXTERNAL_URL is required for webhook mode")

        webhook_url = f"{settings.render_external_url.rstrip('/')}{WEBHOOK_PATH}"
        await bot.set_webhook(
            webhook_url,
            secret_token=settings.webhook_secret,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
        logger.info("Telegram webhook configured: %s", webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Telegram webhook disabled; using long polling.")

    logger.info("MetaTrain initialization completed.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await configure_bot(webhook=True)
    yield
    await bot.session.close()


app = FastAPI(
    title="MetaTrain",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "metatrain-bot", "status": "ok"}


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post(WEBHOOK_PATH)
async def telegram_webhook(
    request: Request,
    telegram_secret: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
) -> Response:
    if settings.webhook_secret and telegram_secret != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    update = Update.model_validate(
        await request.json(),
        context={"bot": bot},
    )
    await dispatcher.feed_update(bot, update)
    return Response(status_code=200)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    await configure_bot(webhook=False)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    if settings.render_external_url:
        uvicorn.run(
            "app.bot.main:app",
            host="0.0.0.0",
            port=10000,
        )
    else:
        asyncio.run(main())
