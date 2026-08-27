import asyncio

from aiogram import Bot, Dispatcher

from app.config.settings import settings
from app.database.connection import init_database
from app.handlers.start import router as start_router


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)

    await init_database()
    print("MetaTrain initialization completed.")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
