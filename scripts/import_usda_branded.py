#!/usr/bin/env python3
"""Import USDA FoodData Central Branded Foods into MetaTrain.

Uses a dedicated synchronous SQLite connection because the importer is a
batch/offline job. Large CSV files are streamed and processed in batches.
"""

import argparse
import csv
import re
import sqlite3
import unicodedata
from pathlib import Path

from app.config.settings import settings
from app.database.connection import init_database

NUTRIENTS = {1008: "calories", 1003: "protein", 1004: "fat", 1005: "carbs", 1079: "fiber"}
BATCH_SIZE = 5000


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
    db.execute("""CREATE TEMP TABLE usda_food_nutrients (
        fdc_id TEXT PRIMARY KEY, calories REAL, protein REAL, fat REAL, carbs REAL, fiber REAL
    )""")
    rows = 0
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        pending = []
        for row in reader:
            fdc_id = row.get("fdc_id") or row.get("food_id")
            nutrient_id = row.get("nutrient_id")
            if not fdc_id or not nutrient_id:
                continue
            try:
                nutrient_id = int(nutrient_id)
                amount = float(row.get("amount") or 0)
            except (TypeError, ValueError):
                continue
            if nutrient_id not in NUTRIENTS:
                continue
            pending.append((fdc_id, nutrient_id, amount))
            rows += 1
            if len(pending) >= BATCH_SIZE:
                _apply_nutrient_batch(db, pending)
                pending.clear()
        if pending:
            _apply_nutrient_batch(db, pending)
    return rows


def _apply_nutrient_batch(db: sqlite3.Connection, rows: list[tuple[str, int, float]]) -> None:
    for fdc_id, nutrient_id, amount in rows:
        column = NUTRIENTS[nutrient_id]
        db.execute(
            f"INSERT INTO temp.usda_food_nutrients (fdc_id, {column}) VALUES (?, ?) "
            f"ON CONFLICT(fdc_id) DO UPDATE SET {column}=excluded.{column}",
            (fdc_id, amount),
        )
    db.commit()


def stage_foods(db: sqlite3.Connection, path: Path) -> int:
    db.execute("DROP TABLE IF EXISTS temp.usda_foods")
    db.execute("CREATE TEMP TABLE usda_foods (fdc_id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT)")
    count = 0
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        pending = []
        for row in reader:
            fdc_id = row.get("fdc_id")
            name = (row.get("description") or row.get("name") or "").strip()
            if not fdc_id or not name:
                continue
            pending.append((fdc_id, name, row.get("food_category_id")))
            count += 1
            if len(pending) >= BATCH_SIZE:
                db.executemany("INSERT OR REPLACE INTO temp.usda_foods VALUES (?, ?, ?)", pending)
                db.commit()
                pending.clear()
        if pending:
            db.executemany("INSERT OR REPLACE INTO temp.usda_foods VALUES (?, ?, ?)", pending)
            db.commit()
    return count


def import_branded_rows(db: sqlite3.Connection, path: Path, source: str) -> int:
    sql = """INSERT INTO food_catalog
        (source, source_id, name, normalized_name, category, brand, preparation,
         calories_per_100g, protein_per_100g, fat_per_100g, carbohydrates_per_100g, fiber_per_100g)
        SELECT ?, b.fdc_id, f.name, ?, f.category,
               NULLIF(TRIM(COALESCE(b.brand_owner, b.brand_name, '')), ''), NULL,
               n.calories, COALESCE(n.protein, 0), COALESCE(n.fat, 0),
               COALESCE(n.carbs, 0), n.fiber
        FROM temp.usda_branded b
        JOIN temp.usda_foods f ON f.fdc_id = b.fdc_id
        JOIN temp.usda_food_nutrients n ON n.fdc_id = b.fdc_id
        WHERE n.calories IS NOT NULL AND n.calories > 0"""
    imported = 0
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        pending = []
        for row in reader:
            fdc_id = row.get("fdc_id")
            if not fdc_id:
                continue
            pending.append((fdc_id, (row.get("brand_owner") or row.get("brand_name") or "").strip() or None))
            if len(pending) >= BATCH_SIZE:
                _insert_branded_batch(db, pending, source, sql)
                imported += len(pending)
                pending.clear()
                if imported % 100000 == 0:
                    print(f"  Imported {imported:,} branded foods...", flush=True)
        if pending:
            _insert_branded_batch(db, pending, source, sql)
            imported += len(pending)
    return imported


def _insert_branded_batch(db: sqlite3.Connection, rows, source: str, sql: str) -> None:
    db.execute("DROP TABLE IF EXISTS temp.usda_branded")
    db.execute("CREATE TEMP TABLE usda_branded (fdc_id TEXT PRIMARY KEY, brand_owner TEXT, brand_name TEXT)")
    db.executemany("INSERT OR REPLACE INTO temp.usda_branded (fdc_id, brand_owner) VALUES (?, ?)", rows)
    db.execute(sql.replace("?, b.fdc_id, f.name, ?,", "?, b.fdc_id, f.name, lower(replace(f.name, ' ', ' ')),"), (source,))
    db.commit()


def import_foods(root: Path, source: str) -> int:
    food_path = find_file(root, "food.csv")
    nutrient_path = find_file(root, "food_nutrient.csv")
    branded_path = find_file(root, "branded_food.csv")
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    try:
        db.execute("PRAGMA foreign_keys = ON")
        init_database_sync(db)
        print("1/3 Staging nutrient values from food_nutrient.csv...", flush=True)
        nutrient_count = stage_nutrients(db, nutrient_path)
        print(f"  Staged {nutrient_count:,} relevant nutrient rows.", flush=True)
        print("2/3 Staging food metadata from food.csv...", flush=True)
        food_count = stage_foods(db, food_path)
        print(f"  Staged {food_count:,} food rows.", flush=True)
        print("3/3 Importing branded foods...", flush=True)
        imported = import_branded_rows(db, branded_path, source)
        db.execute("DROP TABLE IF EXISTS temp.usda_food_nutrients")
        db.execute("DROP TABLE IF EXISTS temp.usda_foods")
        db.commit()
        return imported
    finally:
        db.close()


def init_database_sync(db: sqlite3.Connection) -> None:
    db.executescript("""
    CREATE TABLE IF NOT EXISTS food_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, source_id TEXT NOT NULL,
        name TEXT NOT NULL, normalized_name TEXT NOT NULL, category TEXT, brand TEXT, preparation TEXT,
        calories_per_100g REAL NOT NULL DEFAULT 0, protein_per_100g REAL NOT NULL DEFAULT 0,
        fat_per_100g REAL NOT NULL DEFAULT 0, carbohydrates_per_100g REAL NOT NULL DEFAULT 0,
        fiber_per_100g REAL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(source, source_id)
    );
    CREATE INDEX IF NOT EXISTS idx_food_catalog_normalized_name ON food_catalog(normalized_name);
    CREATE TABLE IF NOT EXISTS food_aliases (
        id INTEGER PRIMARY KEY AUTOINCREMENT, food_id INTEGER NOT NULL, alias TEXT NOT NULL,
        normalized_alias TEXT NOT NULL, UNIQUE(food_id, normalized_alias),
        FOREIGN KEY(food_id) REFERENCES food_catalog(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_food_aliases_normalized ON food_aliases(normalized_alias);
    """)
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--source", default="usda-branded")
    args = parser.parse_args()
    try:
        count = import_foods(args.root, args.source)
    except (sqlite3.Error, OSError) as exc:
        raise SystemExit(f"Import failed: {exc}") from exc
    print(f"Imported/updated {count:,} branded foods from {args.source}")


if __name__ == "__main__":
    main()
