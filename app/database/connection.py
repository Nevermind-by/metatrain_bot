from pathlib import Path

import aiosqlite

from app.config.settings import settings


async def get_connection() -> aiosqlite.Connection:
    database_path = Path(settings.database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = await aiosqlite.connect(database_path)
    connection.row_factory = aiosqlite.Row
    await connection.execute("PRAGMA foreign_keys = ON")
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
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                gender TEXT NOT NULL,
                age INTEGER NOT NULL,
                height_cm REAL NOT NULL,
                weight_kg REAL NOT NULL,
                activity_level TEXT NOT NULL DEFAULT 'sedentary',
                goal TEXT NOT NULL,
                calories INTEGER NOT NULL,
                protein INTEGER NOT NULL,
                fat INTEGER NOT NULL,
                carbohydrates INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        columns = await connection.execute_fetchall("PRAGMA table_info(user_profiles)")
        column_names = {row[1] for row in columns}
        if "activity_level" not in column_names:
            await connection.execute(
                "ALTER TABLE user_profiles ADD COLUMN activity_level TEXT NOT NULL DEFAULT 'sedentary'"
            )
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS food_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                meal TEXT NOT NULL,
                product_name TEXT NOT NULL,
                grams REAL NOT NULL CHECK (grams > 0),
                calories REAL NOT NULL CHECK (calories >= 0),
                protein REAL NOT NULL CHECK (protein >= 0),
                fat REAL NOT NULL CHECK (fat >= 0),
                carbohydrates REAL NOT NULL CHECK (carbohydrates >= 0),
                eaten_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        await connection.commit()
