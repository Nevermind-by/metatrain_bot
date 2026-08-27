from pathlib import Path

import aiosqlite

from app.config.settings import settings


async def get_connection() -> aiosqlite.Connection:
    database_path = Path(settings.database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = await aiosqlite.connect(database_path)
    connection.row_factory = aiosqlite.Row
    return connection


async def init_database() -> None:
    async with await get_connection() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await connection.commit()
