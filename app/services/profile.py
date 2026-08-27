from app.calculators.nutrition import calculate_nutrition
from app.models.profile import UserProfile
from app.repositories.profile import ProfileRepository


class ProfileService:
    def __init__(self, repository: ProfileRepository | None = None) -> None:
        self.repository = repository or ProfileRepository()

    async def create_profile(
        self,
        *,
        user_id: int,
        gender: str,
        age: int,
        height_cm: float,
        weight_kg: float,
        goal: str,
    ) -> UserProfile:
        nutrition = calculate_nutrition(
            gender=gender,
            age=age,
            height_cm=height_cm,
            weight_kg=weight_kg,
            goal=goal,
        )
        profile = UserProfile(
            user_id=user_id,
            gender=gender,
            age=age,
            height_cm=height_cm,
            weight_kg=weight_kg,
            goal=goal,
            calories=nutrition.calories,
            protein=nutrition.protein,
            fat=nutrition.fat,
            carbohydrates=nutrition.carbohydrates,
        )
        return await self.repository.upsert(profile)
