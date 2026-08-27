from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class User:
    id: int | None
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
