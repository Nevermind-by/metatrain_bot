"""Search normalization for the multilingual food catalog.

USDA FoodData Central names are predominantly English. Telegram users may
search in Russian, so common Russian food terms are expanded to their English
counterparts before querying the catalog. The original query is always kept,
so English search continues to work unchanged.
"""

from __future__ import annotations

import re


# Common Russian food terms and phrases used by the first catalog UX.
# This is intentionally kept separate from the USDA import: the source data
# remains untouched and can be re-imported at any time.
RUSSIAN_TO_ENGLISH: dict[str, str] = {
    "куриная грудка": "chicken breast",
    "куриная ножка": "chicken drumstick",
    "куриная голень": "chicken drumstick",
    "куриное бедро": "chicken thigh",
    "куриное крыло": "chicken wing",
    "куриное филе": "chicken breast",
    "курица": "chicken",
    "курочку": "chicken",
    "курочка": "chicken",
    "куриный": "chicken",
    "куриная": "chicken",
    "куриное": "chicken",
    "говядина": "beef",
    "свинина": "pork",
    "индейка": "turkey",
    "рыба": "fish",
    "лосось": "salmon",
    "семга": "salmon",
    "сёмга": "salmon",
    "тунец": "tuna",
    "креветка": "shrimp",
    "креветки": "shrimp",
    "яйцо": "egg",
    "яйца": "egg",
    "рис": "rice",
    "рис белый": "white rice",
    "рис коричневый": "brown rice",
    "гречка": "buckwheat",
    "гречневая крупа": "buckwheat",
    "овсянка": "oatmeal",
    "овсяная каша": "oatmeal",
    "овсяные хлопья": "oats",
    "макароны": "pasta",
    "паста": "pasta",
    "хлеб": "bread",
    "сыр": "cheese",
    "творог": "cottage cheese",
    "йогурт": "yogurt",
    "молоко": "milk",
    "кефир": "kefir",
    "сметана": "sour cream",
    "масло сливочное": "butter",
    "сливочное масло": "butter",
    "масло оливковое": "olive oil",
    "оливковое масло": "olive oil",
    "масло подсолнечное": "sunflower oil",
    "подсолнечное масло": "sunflower oil",
    "картофель": "potato",
    "картошка": "potato",
    "помидор": "tomato",
    "помидоры": "tomato",
    "огурец": "cucumber",
    "огурцы": "cucumber",
    "авокадо": "avocado",
    "банан": "banana",
    "бананы": "banana",
    "яблоко": "apple",
    "яблоки": "apple",
    "апельсин": "orange",
    "апельсины": "orange",
    "овощи": "vegetable",
    "фрукты": "fruit",
    "орехи": "nuts",
    "арахис": "peanut",
    "миндаль": "almond",
    "мед": "honey",
    "мёд": "honey",
    "сахар": "sugar",
}


def search_terms(query: str) -> list[str]:
    """Return the original query plus useful English equivalents."""
    normalized = " ".join(query.casefold().split()).strip()
    if not normalized:
        return []

    terms: list[str] = [normalized]

    # Prefer phrase matches first, then individual words. This allows
    # "куриная грудка" -> "chicken breast" while still handling "грудка".
    phrases = sorted(RUSSIAN_TO_ENGLISH.items(), key=lambda pair: len(pair[0]), reverse=True)
    for russian, english in phrases:
        if russian in normalized:
            terms.append(english)

    for word in re.findall(r"[\w-]+", normalized, flags=re.UNICODE):
        english = RUSSIAN_TO_ENGLISH.get(word)
        if english:
            terms.append(english)

    # Preserve order and remove duplicates.
    return list(dict.fromkeys(terms))
