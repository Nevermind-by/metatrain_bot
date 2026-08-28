#!/usr/bin/env python3
"""Import USDA FoodData Central Branded Foods into MetaTrain.

Streams the large USDA CSV files and stages only the required macro nutrients
and food metadata in temporary SQLite tables. No multi-hundred-MB CSV is
loaded into Python memory.

Usage:
    uv run python scripts/import_usda_branded.py ~/Downloads/usda-branded
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
    1008: "calories",
    1003: "protein",
    1004: "fat",
    1005: "carbs",
    1079: "fiber",
}
BATCH_SIZE = 2000


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def find_file(root: Path, filename: str) -> Path:
    matches = list(root.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"Could not find {filename} under {root}")
    return matches[0]


def stage_nutrients(db: sqlite3.Connection, path: Path) -> int:
    db.execute("DROP TABLE IF EXISTS temp.usda_food_nutrients")
    db.execute(
        """CREATE TEMP TABLE usda_food_nutrients (
            fdc_id TEXT PRIMARY KEY,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL,
            fiber REAL
        )"""
    )
    upsert = """INSERT INTO temp.usda_food_nutrients
        (fdc_id, calories, protein, fat, carbs, fiber)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(fdc_id) DO UPDATE SET
            calories = COALESCE(excluded.calories, calories),
            protein = COALESCE(excluded.protein, protein),
            fat = COALESCE(excluded.fat, fat),
            carbs = COALESCE(excluded.carbs, carbs),
            fiber = COALESCE(excluded.fiber, fiber)"""
    pending: list[tuple[str, int, float]] = []
    rows = 0
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            fdc_id = row.get("fdc_id") or row.get("food_id")
            nutrient_id = row.get("nutrient_id")
            if not fdc_id or not nutrient_id:
                continue
            try:
                nutrient_id_int = int(nutrient_id)
                if nutrient_id_int not in NUTRIENTS:
                    continue
                amount = float(row.get("amount") or 0)
            except (TypeError, ValueError):
                continue
            pending.append((fdc_id, nutrient_id_int, amount))
            rows += 1
            if len(pending) >= BATCH_SIZE:
                _apply_nutrient_batch(db, upsert, pending)
                pending.clear()
    if pending:
        _apply_nutrient_batch(db, upsert, pending)
    return rows


def _apply_nutrient_batch(
    db: sqlite3.Connection, upsert: str, rows: list[tuple[str, int, float]]
) -> None:
    for fdc_id, nutrient_id, amount in rows:
        values = [None] * 5
        values[list(NUTRIENTS).index(nutrient_id)] = amount
        db.execute(upsert, (fdc_id, *values))
    db.commit()


def stage_foods(db: sqlite3.Connection, path: Path) -> int:
    db.execute("DROP TABLE IF EXISTS temp.usda_foods")
    db.execute(
        """CREATE TEMP TABLE usda_foods (
            fdc_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT
        )"""
    )
    pending: list[tuple[str, str, str | None]] = []
    count = 0
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            fdc_id = row.get("fdc_id")
            name = (row.get("description") or row.get("name") or "").strip()
            if not fdc_id or not name:
                continue
            pending.append((fdc_id, name, row.get("food_category_id")))
            count += 1
            if len(pending) >= BATCH_SIZE:
                db.executemany(
                    "INSERT OR REPLACE INTO temp.usda_foods (fdc_id, name, category) VALUES (?, ?, ?)",
                    pending,
                )
                db.commit()
                pending.clear()
    if pending:
        db.executemany(
            "INSERT OR REPLACE INTO temp.usda_foods (fdc_id, name, category) VALUES (?, ?, ?)",
            pending,
        )
        db.commit()
    return count


def import_branded_rows(db: sqlite3.Connection, path: Path, source: str) -> int:
    sql = """INSERT INTO food_catalog
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
            updated_at=CURRENT_TIMESTAMP"""
    pending = []
    imported = 0
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            fdc_id = row.get("fdc_id")
            if not fdc_id:
                continue
            food = db.execute(
                "SELECT name, category FROM temp.usda_foods WHERE fdc_id = ?", (fdc_id,)
            ).fetchone()
            nutrient = db.execute(
                "SELECT calories, protein, fat, carbs, fiber FROM temp.usda_food_nutrients WHERE fdc_id = ?",
                (fdc_id,),
            ).fetchone()
            if food is None or nutrient is None or nutrient[0] is None or nutrient[0] <= 0:
                continue
            name = food[0]
            pending.append(
                (
                    source,
                    fdc_id,
                    name,
                    normalize(name),
                    food[1],
                    (row.get("brand_owner") or row.get("brand_name") or "").strip() or None,
                    None,
                    nutrient[0] or 0,
                    nutrient[1] or 0,
                    nutrient[2] or 0,
                    nutrient[3] or 0,
                    nutrient[4] or 0,
                )
            )
            if len(pending) >= BATCH_SIZE:
                db.executemany(sql, pending)
                db.commit()
                imported += len(pending)
                print(f"Imported {imported:,} branded foods...", flush=True)
                pending.clear()
    if pending:
        db.executemany(sql, pending)
        db.commit()
        imported += len(pending)
    return imported


async def import_foods(root: Path, source: str) -> int:
    food_path = find_file(root, "food.csv")
    nutrient_path = find_file(root, "food_nutrient.csv")
    branded_path = find_file(root, "branded_food.csv")

    await init_database()
    async with await get_connection() as connection:
        db = connection._conn
        print("1/3 Staging nutrient values from food_nutrient.csv...")
        nutrient_count = await asyncio.to_thread(stage_nutrients, db, nutrient_path)
        print(f"  Staged {nutrient_count:,} relevant nutrient rows.")
        print("2/3 Staging food metadata from food.csv...")
        food_count = await asyncio.to_thread(stage_foods, db, food_path)
        print(f"  Staged {food_count:,} food rows.")
        print("3/3 Importing branded foods...")
        imported = await asyncio.to_thread(import_branded_rows, db, branded_path, source)
        await connection.execute("DROP TABLE IF EXISTS temp.usda_food_nutrients")
        await connection.execute("DROP TABLE IF EXISTS temp.usda_foods")
        await connection.commit()
    return imported


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--source", default="usda-branded")
    args = parser.parse_args()
    try:
        count = asyncio.run(import_foods(args.root, args.source))
    except (sqlite3.Error, OSError) as exc:
        raise SystemExit(f"Import failed: {exc}") from exc
    print(f"Imported/updated {count:,} branded foods from {args.source}")


if __name__ == "__main__":
    main()
