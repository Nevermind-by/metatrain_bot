#!/usr/bin/env python3
"""Import USDA FoodData Central Branded Foods into MetaTrain.

The Branded Foods download is large, so this importer streams CSV files and
keeps only the nutrients MetaTrain needs. It first stages those nutrient
values in SQLite, then imports food and branded metadata in batches.

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
    1008: "calories_per_100g",
    1003: "protein_per_100g",
    1004: "fat_per_100g",
    1005: "carbohydrates_per_100g",
    1079: "fiber_per_100g",
}
BATCH_SIZE = 1000


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

    pending: dict[str, list[float]] = {}
    rows = 0
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        nutrient_columns = {str(key): index for index, key in NUTRIENTS.items()}
        for row in reader:
            fdc_id = row.get("fdc_id") or row.get("food_id")
            nutrient_id = row.get("nutrient_id")
            if not fdc_id or not nutrient_id:
                continue
            target = nutrient_columns.get(str(nutrient_id))
            if target is None:
                continue
            try:
                amount = float(row.get("amount") or 0)
            except (TypeError, ValueError):
                continue
            values = pending.setdefault(fdc_id, [0.0] * len(NUTRIENTS))
            values[list(NUTRIENTS).index(int(nutrient_id))] = amount
            rows += 1
            if len(pending) >= BATCH_SIZE:
                db.executemany(
                    """INSERT OR REPLACE INTO temp.usda_food_nutrients
                    (fdc_id, calories, protein, fat, carbs, fiber)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    [(key, *values) for key, values in pending.items()],
                )
                db.commit()
                pending.clear()

    if pending:
        db.executemany(
            """INSERT OR REPLACE INTO temp.usda_food_nutrients
            (fdc_id, calories, protein, fat, carbs, fiber)
            VALUES (?, ?, ?, ?, ?, ?)""",
            [(key, *values) for key, values in pending.items()],
        )
        db.commit()
    return rows


def read_branded(path: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            fdc_id = row.get("fdc_id")
            if not fdc_id:
                continue
            result[fdc_id] = {
                "brand": (row.get("brand_owner") or row.get("brand_name") or "").strip(),
                "brand_name": (row.get("brand_name") or "").strip(),
                "category": (row.get("branded_food_category") or "").strip(),
                "serving_size": (row.get("serving_size") or "").strip(),
                "serving_unit": (row.get("serving_size_unit") or "").strip(),
                "household_serving": (row.get("household_serving_fulltext") or "").strip(),
                "gtin_upc": (row.get("gtin_upc") or "").strip(),
            }
    return result


async def import_foods(root: Path, source: str) -> int:
    food_path = find_file(root, "food.csv")
    nutrient_path = find_file(root, "food_nutrient.csv")
    branded_path = find_file(root, "branded_food.csv")

    await init_database()
    async with await get_connection() as connection:
        db = connection._conn
        print("Staging calories and macros from food_nutrient.csv...")
        nutrient_rows = await asyncio.to_thread(stage_nutrients, db, nutrient_path)
        print(f"Staged {nutrient_rows:,} relevant nutrient rows.")

        branded = await asyncio.to_thread(read_branded, branded_path)
        print(f"Loaded {len(branded):,} branded metadata rows.")

        imported = 0
        pending = []
        with food_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                source_id = row.get("fdc_id")
                name = (row.get("description") or row.get("name") or "").strip()
                if not source_id or not name or source_id not in branded:
                    continue
                nutrient = db.execute(
                    "SELECT calories, protein, fat, carbs, fiber FROM temp.usda_food_nutrients WHERE fdc_id = ?",
                    (source_id,),
                ).fetchone()
                if nutrient is None or nutrient[0] <= 0:
                    continue
                meta = branded[source_id]
                normalized = normalize(name)
                pending.append(
                    (
                        source,
                        source_id,
                        name,
                        normalized,
                        row.get("food_category_id"),
                        meta["brand"],
                        None,
                        nutrient[0],
                        nutrient[1],
                        nutrient[2],
                        nutrient[3],
                        nutrient[4],
                    )
                )
                if len(pending) >= BATCH_SIZE:
                    await connection.executemany(
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
                        pending,
                    )
                    await connection.commit()
                    imported += len(pending)
                    print(f"Imported {imported:,} branded foods...", flush=True)
                    pending.clear()

        if pending:
            await connection.executemany(
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
                pending,
            )
            await connection.commit()
            imported += len(pending)

        await connection.execute("DROP TABLE IF EXISTS temp.usda_food_nutrients")
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
