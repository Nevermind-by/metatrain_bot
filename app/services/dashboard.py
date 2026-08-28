from datetime import UTC, datetime, timedelta

from app.services.food import FoodService
from app.services.profile import ProfileService
from app.services.weight import WeightService
from app.services.workout import WorkoutService


class DashboardService:
    def __init__(self) -> None:
        self.food = FoodService(); self.profile = ProfileService(); self.weight = WeightService(); self.workout = WorkoutService()

    async def build(self, user_id: int, lang: str = "en") -> str:
        profile = await self.profile.get_profile(user_id); foods = await self.food.today(user_id); totals = self.food.totals(foods); latest_weight = await self.weight.latest(user_id); workouts = await self.workout.recent(user_id, 50)
        since = datetime.now(UTC) - timedelta(days=7); weekly_workouts = [item for item in workouts if item.performed_at >= since]
        if lang == "ru":
            lines = ["🏠 <b>Твой день</b>", "", "🔥 <b>Питание</b>", f"Калории: <b>{totals['calories']:g}</b>" + (f" / {profile.calories} ккал" if profile else " ккал"), f"🥩 Белки: {totals['protein']:g} г" + (f" / {profile.protein} г" if profile else ""), f"🥑 Жиры: {totals['fat']:g} г" + (f" / {profile.fat} г" if profile else ""), f"🍚 Углеводы: {totals['carbohydrates']:g} г" + (f" / {profile.carbohydrates} г" if profile else ""), "", f"⚖️ <b>Вес:</b> {latest_weight.weight_kg:g} кг" if latest_weight else "⚖️ <b>Вес:</b> пока нет измерений", f"🏋️ <b>Тренировок за 7 дней:</b> {len(weekly_workouts)}", "", "Выбери, что хочешь сделать:"]
        else:
            lines = ["🏠 <b>Your day</b>", "", "🔥 <b>Nutrition</b>", f"Calories: <b>{totals['calories']:g}</b>" + (f" / {profile.calories} kcal" if profile else " kcal"), f"🥩 Protein: {totals['protein']:g} g" + (f" / {profile.protein} g" if profile else ""), f"🥑 Fat: {totals['fat']:g} g" + (f" / {profile.fat} g" if profile else ""), f"🍚 Carbs: {totals['carbohydrates']:g} g" + (f" / {profile.carbohydrates} g" if profile else ""), "", f"⚖️ <b>Weight:</b> {latest_weight.weight_kg:g} kg" if latest_weight else "⚖️ <b>Weight:</b> no measurements yet", f"🏋️ <b>Workouts in 7 days:</b> {len(weekly_workouts)}", "", "Choose what you want to do:"]
        return "\n".join(lines)
