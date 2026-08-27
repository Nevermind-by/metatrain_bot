from datetime import datetime, timedelta, timezone

from app.services.food import FoodService
from app.services.profile import ProfileService
from app.services.weight import WeightService
from app.services.workout import WorkoutService


class DashboardService:
    def __init__(self) -> None:
        self.food = FoodService()
        self.profile = ProfileService()
        self.weight = WeightService()
        self.workout = WorkoutService()

    async def build(self, user_id: int) -> str:
        profile = await self.profile.get_profile(user_id)
        foods = await self.food.today(user_id)
        totals = self.food.totals(foods)
        latest_weight = await self.weight.latest(user_id)
        workouts = await self.workout.recent(user_id, 50)
        since = datetime.now(timezone.utc) - timedelta(days=7)
        weekly_workouts = [item for item in workouts if item.performed_at >= since]

        lines = ["📊 <b>Сегодня</b>", ""]
        lines.append(f"🔥 Калории: {totals['calories']:g}" + (f" / {profile.calories}" if profile else ""))
        lines.append(f"🥩 Белки: {totals['protein']:g} г" + (f" / {profile.protein} г" if profile else ""))
        lines.append(f"🥑 Жиры: {totals['fat']:g} г" + (f" / {profile.fat} г" if profile else ""))
        lines.append(f"🍚 Углеводы: {totals['carbohydrates']:g} г" + (f" / {profile.carbohydrates} г" if profile else ""))
        lines.append("")
        lines.append(f"⚖️ Вес: {latest_weight.weight_kg:g} кг" if latest_weight else "⚖️ Вес: нет измерений")
        lines.append(f"🏋️ Тренировок за 7 дней: {len(weekly_workouts)}")
        return "\n".join(lines)
