from datetime import datetime

from app.database.connection import get_connection
from app.models.user import User


class UserRepository:
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()

        if row is None:
            return None

        return self._to_model(row)

    async def create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> User:
        async with await get_connection() as connection:
            await connection.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_id, username, first_name, last_name),
            )
            await connection.commit()

        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            raise RuntimeError("User was created but could not be loaded")
        return user

    @staticmethod
    def _to_model(row) -> User:
        return User(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
