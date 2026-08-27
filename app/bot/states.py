from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    gender = State()
    age = State()
    height = State()
    weight = State()
    goal = State()
