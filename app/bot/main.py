import asyncio

from aiogram import Bot, Dispatcher

from app.config.settings import settings
from app.database.connection import init_database
from app.handlers.dashboard import router as dashboard_router
from app.handlers.food import router as food_router
from app.handlers.history import router as history_router
from app.handlers.products import router as products_router
from app.handlers.profile import router as profile_router
from app.handlers.progress import router as progress_router
from app.handlers.recipe import router as recipe_router
from app.handlers.start import router as start_router
from app.handlers.workout import router as workout_router


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    for router in (start_router, profile_router, food_router, products_router, recipe_router, progress_router, dashboard_router, history_router, workout_router):
        dispatcher.include_router(router)

    await init_database()
    print("MetaTrain initialization completed.")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
