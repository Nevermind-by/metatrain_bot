from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.config.settings import settings


@dataclass(slots=True)
class ParsedFoodItem:
    raw_name: str
    amount: float | None
    unit: str = "g"


MEALS = {
    "завтрак": "breakfast",
    "обед": "lunch",
    "ужин": "dinner",
    "перекус": "snack",
    "breakfast": "breakfast",
    "lunch": "lunch",
    "dinner": "dinner",
    "snack": "snack",
}

QUANTITY_RE = re.compile(
    r"(?P<amount>\d+(?:[.,]\d+)?)\s*(?:г|гр|грамм(?:а|ов)?|g|gram(?:s)?)?\b",
    re.IGNORECASE,
)


def detect_meal(text: str) -> str | None:
    for line in text.splitlines():
        value = re.sub(r"[^\wа-яёА-ЯЁ-]+", " ", line, flags=re.UNICODE).strip().casefold()
        if value in MEALS:
            return MEALS[value]
    return None


def _clean(value: str) -> str:
    value = re.sub(r"^[\s\-–—•*]+|[\s\-–—•*]+$", "", value)
    value = re.sub(r"\s{2,}", " ", value)
    return value.strip(" ,;:")


def _parse_line(line: str) -> ParsedFoodItem | None:
    line = _clean(line)
    if not line or line.casefold() in MEALS:
        return None
    match = QUANTITY_RE.search(line)
    if not match:
        return ParsedFoodItem(line, None)
    amount = float(match.group("amount").replace(",", "."))
    before = _clean(mine[:match.start()])
    after = _clean(line[match.end():])
    name = _clean(f"{before} {after}")
    return ParsedFoodItem(name, amount) if name else None


def parse_food_text(text: str) -> list[ParsedFoodItem]:
    items: list[ParsedFoodItem] = []
    for line in text.splitlines():
        parsed = _parse_line(line)
        if parsed:
            items.append(parsed)

    if len(items) <= 1 and len(QUANTITY_RE.findall(text)) > 1:
        items = []
        for match in QUANTITY_RE.finditer(text):
            left = text[max(0, match.start() - 70):match.start()]
            candidate = re.split(r",|;|\s+и\s+|\s+and\s+", left, flags=re.IGNORECASE)[-1]
            candidate = re.sub(r"^(?:съел|съела|потом|затем)\s+", "", candidate, flags=re.IGNORECASE)
            name = _clean(candidate)
            if name:
                items.append(ParsedFoodItem(name, float(match.group("amount").replace(",", "."))))
    return items


def _json_output(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    return json.loads(text)


async def extract_food_with_ai(text: str, image_data_url: str | None = None) -> list[ParsedFoodItem]:
    if not settings.openai_api_key:
        return parse_food_text(text)

    instruction = (
        "Extract food items from the user message and optional photo. "
        'Return JSON only: {"items":[{"name":"...", "amount":150, "unit":"g"}]}. '
        "Preserve explicit quantities exactly. Keep preparation, fat percentage and useful details. "
        "Ignore meal names. Never invent ingredients that are not stated or reasonably visible. "
        "Photo is additional context and must not override explicit text quantities."
    )
    content = [{"type": "input_text", "text": instruction + "\n\n" + (text.strip() or "(inspect photo)")}]
    if image_data_url:
        content.append({"type": "input_image", "image_url": image_data_url, "detail": "high"})

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={"model": settings.openai_model, "input": [{"role": "user", "content": content}]},
            )
            response.raise_for_status()
            output = response.json().get("output_text", "")
        data = _json_output(output)
        result = []
        for item in data.get("items", []):
            name = str(item.get("name", "")).strip()
            if name:
                amount = item.get("amount")
                result.append(ParsedFoodItem(name, float(amount) if amount is not None else None))
        return result or parse_food_text(text)
    except (httpx.HTTPError, ValueError, TypeError, json.JSONDecodeError, KeyError):
        return parse_food_text(text)
