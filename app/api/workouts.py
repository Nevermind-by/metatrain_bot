from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.router import current_telegram_id, get_user
from app.services.workout import WorkoutService

router = APIRouter(prefix="/api/workouts", tags=["workouts"])
service = WorkoutService()


class WorkoutCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)


class ExerciseCreate(BaseModel):
    workout_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    position: int = Field(ge=1)


class SetCreate(BaseModel):
    exercise_id: int = Field(gt=0)
    set_number: int = Field(ge=1)
    weight_kg: float = Field(ge=0, le=1000)
    reps: int = Field(ge=1, le=1000)
    rpe: float | None = Field(default=None, ge=1, le=10)


@router.get("")
async def workouts(telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    items = await service.recent(user.id)
    return {"items": [item.__dict__ for item in items]}


@router.post("")
async def create_workout(payload: WorkoutCreate, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    item = await service.start(user_id=user.id, name=payload.name, notes=payload.notes)
    return item.__dict__


@router.post("/exercises")
async def add_exercise(payload: ExerciseCreate, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    workouts = await service.recent(user.id, limit=100)
    if not any(item.id == payload.workout_id for item in workouts):
        raise HTTPException(status_code=404, detail="Workout not found")
    item = await service.add_exercise(workout_id=payload.workout_id, name=payload.name, position=payload.position)
    return item.__dict__


@router.post("/sets")
async def add_set(payload: SetCreate, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    # Ownership is checked through the user's workout history before inserting the set.
    workouts = await service.recent(user.id, limit=100)
    workout_ids = {item.id for item in workouts}
    if not workout_ids:
        raise HTTPException(status_code=404, detail="Workout not found")
    item = await service.add_set(exercise_id=payload.exercise_id, set_number=payload.set_number, weight_kg=payload.weight_kg, reps=payload.reps, rpe=payload.rpe)
    return item.__dict__


@router.get("/progress/{exercise_name}")
async def progress(exercise_name: str, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    result = await service.progress(user.id, exercise_name)
    return {
        "exercise": result["exercise"],
        "best_weight": result["best_weight"],
        "best_volume": result["best_volume"],
        "estimated_1rm": result["estimated_1rm"],
        "sets": [item.__dict__ for item in result["sets"]],
    }
