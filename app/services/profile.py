from app.calculators.nutrition import calculate_nutrition
from app.models.profile import UserProfile
from app.repositories.profile import ProfileRepository


class ProfileService:
    def __init__(self, repository: ProfileRepository | None = None) -> None:
        self.repository = repository or ProfileRepository()

    async def create_profile(self, *, user_id: int, gender: str, age: int, height_cm: float, weight_kg: float, activity_level: str, goal: str) -> UserProfile:
        return await self._save(user_id, gender, age, height_cm, weight_kg, activity_level, goal)

    async def get_profile(self, user_id: int) -> UserProfile | None:
        return await self.repository.get_by_user_id(user_id)

    async def update_profile(self, user_id: int, *, gender: str, age: int, height_cm: float, weight_kg: float, activity_level: str, goal: str) -> UserProfile:
        return await self._save(user_id, gender, age, height_cm, weight_kg, activity_level, goal)

    async def _save(self, user_id: int, gender: str, age: int, height_cm: float, weight_kg: float, activity_level: str, goal: str) -> UserProfile:
        nutrition = calculate_nutrition(gender=gender, age=age, height_cm=height_cm, weight_kg=weight_kg, activity_level=activity_level, goal=goal)
        profile = UserProfile(user_id=user_id, gender=gender, age=age, height_cm=height_cm, weight_kg=weight_kg, activity_level=activity_level, goal=goal, calories=nutrition.calories, protein=nutrition.protein, fat=nutrition.fat, carbohydrates=nutrition.carbohydrates)
        return await self.repository.upsert(profile)

    def format_profile(self, profile: UserProfile, lang: str = "en") -> str:
        if lang == "ru":
            gender = {"male": "Мужчина", "female": "Женщина"}.get(profile.gender, profile.gender)
            activity = {"sedentary": "Минимальная", "light": "Лёгкая", "moderate": "Средняя", "high": "Высокая", "very_high": "Очень высокая"}.get(profile.activity_level, profile.activity_level)
            goal = {"lose": "Похудеть", "maintain": "Поддерживать вес", "gain": "Набрать массу"}.get(profile.goal, profile.goal)
            return ("👤 <b>Твой профиль</b>\n\n" f"Пол: {gender}\nВозраст: {profile.age} лет\n" f"Рост: {profile.height_cm:g} см\nВес: {profile.weight_kg:g} кг\n" f"Активность: {activity}\nЦель: {goal}\n\n" "🎯 <b>Твоя дневная норма</b>\n\n" f"🔥 Калории: <b>{profile.calories} ккал</b>\n" f"🥩 Белки: <b>{profile.protein} г</b>\n" f"🥑 Жиры: <b>{profile.fat} г</b>\n" f"🍚 Углеводы: <b>{profile.carbohydrates} г</b>")
        gender = {"male": "Male", "female": "Female"}.get(profile.gender, profile.gender)
        activity = {"sedentary": "Sedentary", "light": "Light", "moderate": "Moderate", "high": "High", "very_high": "Very high"}.get(profile.activity_level, profile.activity_level)
        goal = {"lose": "Lose weight", "maintain": "Maintain weight", "gain": "Gain muscle"}.get(profile.goal, profile.goal)
        return ("👤 <b>Your profile</b>\n\n" f"Gender: {gender}\nAge: {profile.age}\n" f"Height: {profile.height_cm:g} cm\nWeight: {profile.weight_kg:g} kg\n" f"Activity: {activity}\nGoal: {goal}\n\n" "🎯 <b>Your daily target</b>\n\n" f"🔥 Calories: <b>{profile.calories} kcal</b>\n" f"🥩 Protein: <b>{profile.protein} g</b>\n" f"🥑 Fat: <b>{profile.fat} g</b>\n" f"🍚 Carbs: <b>{profile.carbohydrates} g</b>")
