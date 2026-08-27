from aiogram.types import User as TelegramUser

from app.models.user import User
from app.repositories.user import UserRepository


class UserService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self.repository = repository or UserRepository()

    async def register(self, telegram_user: TelegramUser) -> tuple[User, bool]:
        existing = await self.repository.get_by_telegram_id(telegram_user.id)
        if existing is not None:
            return existing, False

        user = await self.repository.create(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
        )
        return user, True
