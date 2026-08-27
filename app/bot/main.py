import asyncio

from aiogram import Bot, Dispatcher

from app.config.settings import settings
from app.database.connection import init_database
from app.handlers.food import router as food_router
from app.handlers.profile import router as profile_router
from app.handlers.progress import router as progress_router
from app.handlers.start import router as start_router


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)
    dispatcher.include_router(profile_router)
    dispatcher.include_router(food_router)
    dispatcher.include_router(progress_router)

    await init_database()
    print("MetaTrain initialization completed.")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
