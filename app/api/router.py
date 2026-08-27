from fastapi import APIRouter, HTTPException

from app.api.schemas import DashboardResponse, FoodCreate, WeightCreate
from app.services.dashboard import DashboardService
from app.services.food import FoodService
from app.services.user import UserService
from app.services.weight import WeightService

router = APIRouter(prefix="/api")
user_service = UserService()
dashboard_service = DashboardService()
food_service = FoodService()
weight_service = WeightService()


async def get_user(telegram_id: int):
    user = await user_service.get_by_telegram_id(telegram_id)
    if user is None or user.id is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me")
async def me(telegram_id: int):
    user = await get_user(telegram_id)
    return {"id": user.id, "telegram_id": user.telegram_id, "username": user.username, "first_name": user.first_name}


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(telegram_id: int):
    user = await get_user(telegram_id)
    return DashboardResponse(text=await dashboard_service.build(user.id))


@router.get("/food/today")
async def food_today(telegram_id: int):
    user = await get_user(telegram_id)
    entries = await food_service.today(user.id)
    return {"items": [entry.__dict__ for entry in entries], "totals": food_service.totals(entries)}


@router.post("/food")
async def add_food(payload: FoodCreate, telegram_id: int):
    user = await get_user(telegram_id)
    entry = await food_service.add_product_entry(user_id=user.id, **payload.model_dump())
    return entry.__dict__


@router.get("/weights")
async def weights(telegram_id: int):
    user = await get_user(telegram_id)
    entries = await weight_service.recent(user.id)
    return {"items": [entry.__dict__ for entry in entries]}


@router.post("/weights")
async def add_weight(payload: WeightCreate, telegram_id: int):
    user = await get_user(telegram_id)
    entry = await weight_service.add(user.id, payload.weight_kg)
    return entry.__dict__
