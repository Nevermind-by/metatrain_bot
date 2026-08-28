from dataclasses import dataclass


@dataclass(slots=True)
class ExerciseCatalogItem:
    id: int
    name_ru: str
    name_en: str
    category: str
    muscle_group_ru: str
    muscle_group_en: str
    equipment_ru: str
    equipment_en: str
    aliases_ru: tuple[str, ...] = ()
    aliases_en: tuple[str, ...] = ()
