#!/usr/bin/env python3
"""Import USDA FoodData Central CSV data into MetaTrain.

Download an official FoodData Central CSV archive, extract it, then run:

    uv run python scripts/import_fooddata_central.py /path/to/extracted

The importer expects food.csv and food_nutrient.csv. food_category.csv is
optional. It keeps only the nutrients needed by MetaTrain and stores them per
100 g. Re-running the import is safe because (source, source_id) is unique.
"""

import argparse
import asyncio
import csv
import re
import sqlite3
import unicodedata
from pathlib import Path

from app.database.connection import get_connection, init_database

NUTRIENTS = {
    1008: "calories_per_100g",  # Energy, kcal
    1003: "protein_per_100g",
    1004: "fat_per_100g",
    1005: "carbohydrates_per_100g",
    1079: "fiber_per_100g",
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def find_file(root: Path, filename: str) -> Path:
    matches = list(root.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"Could not find {filename} under {root}")
    return matches[0]


def read_categories(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        result: dict[str, str] = {}
        for row in reader:
            key = row.get("id") or row.get("food_category_id")
            value = row.get("description") or row.get("name")
            if key and value:
                result[key] = value.strip()
        return result


def nutrient_rows(path: Path) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            food_id = row.get("fdc_id") or row.get("food_id")
            nutrient_id = row.get("nutrient_id")
            if not food_id or not nutrient_id:
                continue
            try:
                target = NUTRIENTS.get(int(nutrient_id))
                amount = float(row.get("amount") or 0)
            except (TypeError, ValueError):
                continue
            if target is not None:
                result.setdefault(food_id, {})[target] = amount
    return result


async def import_foods(root: Path, source: str) -> int:
    food_path = find_file(root, "food.csv")
    nutrient_path = find_file(root, "food_nutrient.csv")
    category_path = next(iter(root.rglob("food_category.csv")), None)
    categories = read_categories(category_path)
    nutrients = nutrient_rows(nutrient_path)

    await init_database()
    imported = 0
    async with await get_connection() as connection:
        with food_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                source_id = row.get("fdc_id")
                name = (row.get("description") or row.get("name") or "").strip()
                if not source_id or not name:
                    continue
                values = nutrients.get(source_id, {})
                calories = values.get("calories_per_100g", 0)
                protein = values.get("protein_per_100g", 0)
                fat = values.get("fat_per_100g", 0)
                carbs = values.get("carbohydrates_per_100g", 0)
                # Skip records without an energy value; they are not useful for
                # the first food-tracking release and can be imported later.
                if calories <= 0:
                    continue
                category_id = row.get("food_category_id") or row.get("food_category_id")
                category = categories.get(category_id) if category_id else None
                normalized = normalize(name)
                await connection.execute(
                    """INSERT INTO food_catalog
                    (source, source_id, name, normalized_name, category, brand,
                     preparation, calories_per_100g, protein_per_100g, fat_per_100g,
                     carbohydrates_per_100g, fiber_per_100g)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source, source_id) DO UPDATE SET
                        name=excluded.name,
                        normalized_name=excluded.normalized_name,
                        category=excluded.category,
                        brand=excluded.brand,
                        preparation=excluded.preparation,
                        calories_per_100g=excluded.calories_per_100g,
                        protein_per_100g=excluded.protein_per_100g,
                        fat_per_100g=excluded.fat_per_100g,
                        carbohydrates_per_100g=excluded.carbohydrates_per_100g,
                        fiber_per_100g=excluded.fiber_per_100g,
                        updated_at=CURRENT_TIMESTAMP""",
                    (source, source_id, name, normalized, category,
                     row.get("brand_name"), None, calories, protein, fat, carbs,
                     values.get("fiber_per_100g")),
                )
                imported += 1
        await connection.commit()
    return imported


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="Extracted FoodData Central directory")
    parser.add_argument("--source", default="usda", help="Source label stored in the catalog")
    args = parser.parse_args()
    try:
        count = asyncio.run(import_foods(args.root, args.source))
    except sqlite3.Error as exc:
        raise SystemExit(f"Database error: {exc}") from exc
    print(f"Imported/updated {count} foods from {args.source}")


if __name__ == "__main__":
    main()
