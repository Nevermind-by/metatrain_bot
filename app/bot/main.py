import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

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
from app.handlers.start import router as start_router
from app.handlers.workout import router as workout_router

logger = logging.getLogger(__name__)


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
    BotCommand(command="help", description="Все возможности"),
]


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    for router in (
        start_router,
        main_menu_router,
        profile_router,
        food_router,
        products_router,
        recipe_router,
        progress_router,
        dashboard_router,
        history_router,
        workout_router,
    ):
        dispatcher.include_router(router)

    await bot.set_my_commands(BOT_COMMANDS)
    await init_database()
    logger.info("MetaTrain initialization completed.")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
