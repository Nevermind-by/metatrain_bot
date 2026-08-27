from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class WeightEntry:
    id: int | None
    user_id: int
    weight_kg: float
    measured_at: datetime
