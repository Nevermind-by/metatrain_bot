from app.database.connection import get_connection
from app.models.exercise import ExerciseCatalogItem


EXERCISES = (
    ("bench_press", "Жим штанги лёжа", "Bench press", "chest", "Грудь", "Chest", "Штанга", "Barbell", ("жим лёжа", "жим штанги"), ("bench press", "barbell bench press")),
    ("incline_bench_press", "Жим штанги на наклонной скамье", "Incline barbell bench press", "chest", "Грудь", "Chest", "Штанга", "Barbell", ("жим на наклонной", "наклонный жим"), ("incline bench",)),
    ("dumbbell_bench_press", "Жим гантелей лёжа", "Dumbbell bench press", "chest", "Грудь", "Chest", "Гантели", "Dumbbells", ("жим гантелей",), ("dumbbell bench",)),
    ("incline_dumbbell_press", "Жим гантелей на наклонной скамье", "Incline dumbbell press", "chest", "Грудь", "Chest", "Гантели", "Dumbbells", ("наклонный жим гантелей",), ("incline dumbbell bench",)),
    ("push_up", "Отжимания", "Push-up", "chest", "Грудь", "Chest", "Без оборудования", "Bodyweight", ("отжимания",), ("push ups", "pushup")),
    ("chest_fly", "Разводка с гантелями", "Dumbbell fly", "chest", "Грудь", "Chest", "Гантели", "Dumbbells", ("разводка",), ("dumbbell flyes",)),
    ("cable_crossover", "Сведение рук в кроссовере", "Cable crossover", "chest", "Грудь", "Chest", "Кроссовер", "Cable machine", ("кроссовер на грудь", "сведение в кроссовере"), ("cable fly",)),
    ("pull_up", "Подтягивания", "Pull-up", "back", "Спина", "Back", "Турник", "Pull-up bar", ("подтягивания",), ("pull up", "pullups")),
    ("lat_pulldown", "Тяга верхнего блока", "Lat pulldown", "back", "Спина", "Back", "Тренажёр", "Cable machine", ("верхний блок",), ("lat pull down",)),
    ("barbell_row", "Тяга штанги в наклоне", "Barbell row", "back", "Спина", "Back", "Штанга", "Barbell", ("тяга штанги",), ("bent over row",)),
    ("seated_cable_row", "Тяга горизонтального блока", "Seated cable row", "back", "Спина", "Back", "Тренажёр", "Cable machine", ("горизонтальный блок",), ("cable row",)),
    ("one_arm_dumbbell_row", "Тяга гантели одной рукой", "One-arm dumbbell row", "back", "Спина", "Back", "Гантель", "Dumbbell", ("тяга гантели",), ("one arm row",)),
    ("deadlift", "Становая тяга", "Deadlift", "back", "Спина", "Back", "Штанга", "Barbell", ("становая",), ("deadlift",)),
    ("barbell_squat", "Приседания со штангой", "Barbell squat", "legs", "Ноги", "Legs", "Штанга", "Barbell", ("присед", "приседания со штангой"), ("squat",)),
    ("front_squat", "Фронтальные приседания", "Front squat", "legs", "Ноги", "Legs", "Штанга", "Barbell", ("фронтальный присед",), ("front squat",)),
    ("leg_press", "Жим ногами", "Leg press", "legs", "Ноги", "Legs", "Тренажёр", "Machine", ("жим ногами",), ("leg press",)),
    ("romanian_deadlift", "Румынская тяга", "Romanian deadlift", "legs", "Ноги", "Legs", "Штанга", "Barbell", ("румынская тяга",), ("romanian deadlift", "rdl")),
    ("leg_curl", "Сгибание ног", "Leg curl", "legs", "Ноги", "Legs", "Тренажёр", "Machine", ("сгибание ног",), ("leg curl",)),
    ("leg_extension", "Разгибание ног", "Leg extension", "legs", "Ноги", "Legs", "Тренажёр", "Machine", ("разгибание ног",), ("leg extension",)),
    ("calf_raise", "Подъёмы на носки", "Calf raise", "legs", "Ноги", "Legs", "Тренажёр", "Machine", ("икры", "подъёмы на носки"), ("calf raises",)),
    ("lunges", "Выпады", "Lunges", "legs", "Ноги", "Legs", "Гантели", "Dumbbells", ("выпады",), ("lunges",)),
    ("shoulder_press", "Жим гантелей сидя", "Seated dumbbell shoulder press", "shoulders", "Плечи", "Shoulders", "Гантели", "Dumbbells", ("жим гантелей на плечи",), ("dumbbell shoulder press",)),
    ("barbell_overhead_press", "Жим штанги стоя", "Barbell overhead press", "shoulders", "Плечи", "Shoulders", "Штанга", "Barbell", ("армейский жим", "жим стоя"), ("overhead press", "military press")),
    ("lateral_raise", "Подъёмы гантелей через стороны", "Dumbbell lateral raise", "shoulders", "Плечи", "Shoulders", "Гантели", "Dumbbells", ("махи в стороны", "разведения в стороны"), ("lateral raises",)),
    ("rear_delt_fly", "Разводка на заднюю дельту", "Rear delt fly", "shoulders", "Плечи", "Shoulders", "Гантели", "Dumbbells", ("задняя дельта",), ("rear delt fly",)),
    ("face_pull", "Тяга каната к лицу", "Face pull", "shoulders", "Плечи", "Shoulders", "Кроссовер", "Cable machine", ("фейс пул", "тяга к лицу"), ("face pull",)),
    ("barbell_curl", "Сгибание рук со штангой", "Barbell curl", "arms", "Руки", "Arms", "Штанга", "Barbell", ("подъём штанги на бицепс",), ("barbell biceps curl",)),
    ("dumbbell_curl", "Сгибание рук с гантелями", "Dumbbell curl", "arms", "Руки", "Arms", "Гантели", "Dumbbells", ("подъём гантелей на бицепс",), ("dumbbell biceps curl",)),
    ("hammer_curl", "Молотки", "Hammer curl", "arms", "Руки", "Arms", "Гантели", "Dumbbells", ("молотки", "молотковые сгибания"), ("hammer curls",)),
    ("triceps_pushdown", "Разгибание рук на блоке", "Triceps pushdown", "arms", "Руки", "Arms", "Кроссовер", "Cable machine", ("разгибание на блоке",), ("triceps pushdown", "tricep pushdown")),
    ("skull_crusher", "Французский жим лёжа", "Lying triceps extension", "arms", "Руки", "Arms", "Штанга", "Barbell", ("французский жим",), ("skull crusher", "lying triceps extension")),
    ("dip", "Отжимания на брусьях", "Parallel bar dip", "arms", "Руки", "Arms", "Брусья", "Dip bars", ("брусья", "отжимания на брусьях"), ("dips", "parallel bar dip")),
    ("plank", "Планка", "Plank", "core", "Пресс", "Core", "Без оборудования", "Bodyweight", ("планка",), ("plank",)),
    ("crunch", "Скручивания", "Crunch", "core", "Пресс", "Core", "Без оборудования", "Bodyweight", ("скручивания",), ("crunches",)),
    ("hanging_leg_raise", "Подъём ног в висе", "Hanging leg raise", "core", "Пресс", "Core", "Турник", "Pull-up bar", ("подъём ног в висе",), ("hanging leg raises",)),
    ("cable_crunch", "Скручивания на блоке", "Cable crunch", "core", "Пресс", "Core", "Кроссовер", "Cable machine", ("скручивания на верхнем блоке",), ("cable crunch",)),
)


class ExerciseCatalogRepository:
    async def _ensure(self) -> None:
        async with await get_connection() as connection:
            await connection.execute("""CREATE TABLE IF NOT EXISTS exercise_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name_ru TEXT NOT NULL,
                name_en TEXT NOT NULL,
                category TEXT NOT NULL,
                muscle_group_ru TEXT NOT NULL,
                muscle_group_en TEXT NOT NULL,
                equipment_ru TEXT NOT NULL,
                equipment_en TEXT NOT NULL,
                aliases_ru TEXT NOT NULL DEFAULT '',
                aliases_en TEXT NOT NULL DEFAULT ''
            )""")
            count = await connection.execute_fetchone("SELECT COUNT(*) FROM exercise_catalog")
            if count[0] == 0:
                await connection.executemany(
                    "INSERT INTO exercise_catalog (code,name_ru,name_en,category,muscle_group_ru,muscle_group_en,equipment_ru,equipment_en,aliases_ru,aliases_en) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [(code, ru, en, category, mg_ru, mg_en, eq_ru, eq_en, "|".join(a_ru), "|".join(a_en)) for code, ru, en, category, mg_ru, mg_en, eq_ru, eq_en, a_ru, a_en in EXERCISES],
                )
                await connection.execute("CREATE INDEX IF NOT EXISTS idx_exercise_catalog_category ON exercise_catalog(category)")
                await connection.execute("CREATE INDEX IF NOT EXISTS idx_exercise_catalog_ru ON exercise_catalog(name_ru)")
                await connection.execute("CREATE INDEX IF NOT EXISTS idx_exercise_catalog_en ON exercise_catalog(name_en)")
                await connection.commit()

    async def list_by_category(self, category: str) -> list[ExerciseCatalogItem]:
        await self._ensure()
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM exercise_catalog WHERE category = ? ORDER BY name_ru", (category,))
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    async def get(self, exercise_id: int) -> ExerciseCatalogItem | None:
        await self._ensure()
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM exercise_catalog WHERE id = ?", (exercise_id,))
            row = await cursor.fetchone()
        return self._to_model(row) if row else None

    async def search(self, query: str, limit: int = 20) -> list[ExerciseCatalogItem]:
        await self._ensure()
        normalized = " ".join(query.casefold().split()).strip()
        if not normalized:
            return []
        pattern = f"%{normalized}%"
        async with await get_connection() as connection:
            cursor = await connection.execute(
                """SELECT * FROM exercise_catalog
                   WHERE lower(name_ru) LIKE ? OR lower(name_en) LIKE ? OR lower(aliases_ru) LIKE ? OR lower(aliases_en) LIKE ?
                   ORDER BY length(name_ru), name_ru LIMIT ?""",
                (pattern, pattern, pattern, pattern, limit),
            )
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> ExerciseCatalogItem:
        return ExerciseCatalogItem(
            id=row["id"], name_ru=row["name_ru"], name_en=row["name_en"], category=row["category"],
            muscle_group_ru=row["muscle_group_ru"], muscle_group_en=row["muscle_group_en"],
            equipment_ru=row["equipment_ru"], equipment_en=row["equipment_en"],
            aliases_ru=tuple(filter(None, row["aliases_ru"].split("|"))),
            aliases_en=tuple(filter(None, row["aliases_en"].split("|"))),
        )
