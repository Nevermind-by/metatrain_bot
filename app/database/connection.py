from pathlib import Path

import aiosqlite

from app.config.settings import settings


class _ConnectionContext:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self._connection = connection

    async def __aenter__(self) -> aiosqlite.Connection:
        return self._connection

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self._connection.close()


async def get_connection() -> _ConnectionContext:
    database_path = Path(settings.database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = await aiosqlite.connect(database_path)
    connection.row_factory = aiosqlite.Row
    await connection.execute("PRAGMA foreign_keys = ON")
    return _ConnectionContext(connection)


async def init_database() -> None:
    async with await get_connection() as connection:
        await connection.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL UNIQUE, username TEXT, first_name TEXT, last_name TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        await connection.execute("""CREATE TABLE IF NOT EXISTS user_profiles (user_id INTEGER PRIMARY KEY, gender TEXT NOT NULL, age INTEGER NOT NULL, height_cm REAL NOT NULL, weight_kg REAL NOT NULL, activity_level TEXT NOT NULL DEFAULT 'sedentary', goal TEXT NOT NULL, calories INTEGER NOT NULL, protein INTEGER NOT NULL, fat INTEGER NOT NULL, carbohydrates INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)""")
        columns = await connection.execute_fetchall("PRAGMA table_info(user_profiles)")
        if "activity_level" not in {row[1] for row in columns}: await connection.execute("ALTER TABLE user_profiles ADD COLUMN activity_level TEXT NOT NULL DEFAULT 'sedentary'")
        await connection.execute("""CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, calories REAL NOT NULL CHECK (calories >= 0), protein REAL NOT NULL CHECK (protein >= 0), fat REAL NOT NULL CHECK (fat >= 0), carbohydrates REAL NOT NULL CHECK (carbohydrates >= 0), UNIQUE(user_id, name), FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)""")
        await connection.execute("""CREATE TABLE IF NOT EXISTS recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, servings INTEGER NOT NULL CHECK (servings > 0), calories REAL NOT NULL CHECK (calories >= 0), protein REAL NOT NULL CHECK (protein >= 0), fat REAL NOT NULL CHECK (fat >= 0), carbohydrates REAL NOT NULL CHECK (carbohydrates >= 0), UNIQUE(user_id, name), FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)""")
        await connection.execute("""CREATE TABLE IF NOT EXISTS recipe_ingredients (id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, product_id INTEGER NOT NULL, grams REAL NOT NULL CHECK (grams > 0), UNIQUE(recipe_id, product_id), FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE)""")
        await connection.execute("""CREATE TABLE IF NOT EXISTS food_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, meal TEXT NOT NULL, product_name TEXT NOT NULL, quantity REAL NOT NULL CHECK (quantity > 0), unit TEXT NOT NULL DEFAULT 'g', calories REAL NOT NULL CHECK (calories >= 0), protein REAL NOT NULL CHECK (protein >= 0), fat REAL NOT NULL CHECK (fat >= 0), carbohydrates REAL NOT NULL CHECK (carbohydrates >= 0), eaten_at TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)""")
        columns = await connection.execute_fetchall("PRAGMA table_info(food_entries)")
        names = {row[1] for row in columns}
        if "quantity" not in names: await connection.execute("ALTER TABLE food_entries ADD COLUMN quantity REAL NOT NULL DEFAULT 100")
        if "unit" not in names: await connection.execute("ALTER TABLE food_entries ADD COLUMN unit TEXT NOT NULL DEFAULT 'g'")

        await connection.execute("""CREATE TABLE IF NOT EXISTS food_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            category TEXT,
            brand TEXT,
            preparation TEXT,
            calories_per_100g REAL NOT NULL DEFAULT 0 CHECK (calories_per_100g >= 0),
            protein_per_100g REAL NOT NULL DEFAULT 0 CHECK (protein_per_100g >= 0),
            fat_per_100g REAL NOT NULL DEFAULT 0 CHECK (fat_per_100g >= 0),
            carbohydrates_per_100g REAL NOT NULL DEFAULT 0 CHECK (carbohydrates_per_100g >= 0),
            fiber_per_100g REAL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, source_id)
        )""")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_food_catalog_normalized_name ON food_catalog(normalized_name)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_food_catalog_category ON food_catalog(category)")
        await connection.execute("""CREATE TABLE IF NOT EXISTS food_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_id INTEGER NOT NULL,
            alias TEXT NOT NULL,
            normalized_alias TEXT NOT NULL,
            UNIQUE(food_id, normalized_alias),
            FOREIGN KEY (food_id) REFERENCES food_catalog(id) ON DELETE CASCADE
        )""")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_food_aliases_normalized ON food_aliases(normalized_alias)")

        await connection.execute("""CREATE TABLE IF NOT EXISTS weight_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, weight_kg REAL NOT NULL CHECK (weight_kg >= 30 AND weight_kg <= 300), measured_at TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)""")
        await connection.execute("""CREATE TABLE IF NOT EXISTS workout_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, duration_minutes INTEGER, calories_burned INTEGER, notes TEXT, performed_at TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)""")
        await connection.execute("""CREATE TABLE IF NOT EXISTS workout_exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, workout_id INTEGER NOT NULL, name TEXT NOT NULL, position INTEGER NOT NULL, FOREIGN KEY (workout_id) REFERENCES workout_entries(id) ON DELETE CASCADE)""")
        await connection.execute("""CREATE TABLE IF NOT EXISTS workout_sets (id INTEGER PRIMARY KEY AUTOINCREMENT, exercise_id INTEGER NOT NULL, set_number INTEGER NOT NULL, weight_kg REAL NOT NULL CHECK (weight_kg >= 0), reps INTEGER NOT NULL CHECK (reps > 0), rpe REAL CHECK (rpe IS NULL OR (rpe >= 1 AND rpe <= 10)), UNIQUE(exercise_id, set_number), FOREIGN KEY (exercise_id) REFERENCES workout_exercises(id) ON DELETE CASCADE)""")
        await connection.commit()
