from datetime import datetime

from app.database.connection import get_connection
from app.models.profile import UserProfile


class ProfileRepository:
    async def upsert(self, profile: UserProfile) -> UserProfile:
        async with await get_connection() as connection:
            await connection.execute(
                """
                INSERT INTO user_profiles (
                    user_id, gender, age, height_cm, weight_kg, goal,
                    calories, protein, fat, carbohydrates
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    gender = excluded.gender,
                    age = excluded.age,
                    height_cm = excluded.height_cm,
                    weight_kg = excluded.weight_kg,
                    goal = excluded.goal,
                    calories = excluded.calories,
                    protein = excluded.protein,
                    fat = excluded.fat,
                    carbohydrates = excluded.carbohydrates,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    profile.user_id,
                    profile.gender,
                    profile.age,
                    profile.height_cm,
                    profile.weight_kg,
                    profile.goal,
                    profile.calories,
                    profile.protein,
                    profile.fat,
                    profile.carbohydrates,
                ),
            )
            await connection.commit()

        saved = await self.get_by_user_id(profile.user_id)
        if saved is None:
            raise RuntimeError("Profile was saved but could not be loaded")
        return saved

    async def get_by_user_id(self, user_id: int) -> UserProfile | None:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()

        if row is None:
            return None

        return UserProfile(
            user_id=row["user_id"],
            gender=row["gender"],
            age=row["age"],
            height_cm=row["height_cm"],
            weight_kg=row["weight_kg"],
            goal=row["goal"],
            calories=row["calories"],
            protein=row["protein"],
            fat=row["fat"],
            carbohydrates=row["carbohydrates"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
