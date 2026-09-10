"""Heuristic mapping from Nominatim OSM tags / free text to Nick's fixed
category list. This is a best-effort heuristic, not ground truth - OSM tag
coverage for small/newer businesses is spotty, and titles are sometimes
ambiguous (see handoff doc: "Moonzescope"). Anything that doesn't clearly
map falls into "Other/Uncategorized" for manual review.

`data/category_overrides.json` (Title -> Category) always wins over the
heuristic, so corrections don't get re-litigated on every rerun.
"""

import json
import os

CATEGORIES = [
    "Dining",
    "Coffee/Bakery",
    "Bars/Nightlife",
    "Galleries",
    "Museums/Cultural Institutions",
    "Arts/Studios/Event Spaces",
    "Shops/Retail",
    "Parks/Outdoors",
    "Other/Uncategorized",
]

# (osm_category, osm_type) -> our category. `None` as a wildcard for type.
OSM_TAG_MAP = {
    ("tourism", "gallery"): "Galleries",
    ("shop", "art"): "Galleries",
    ("tourism", "museum"): "Museums/Cultural Institutions",
    ("amenity", "theatre"): "Museums/Cultural Institutions",
    ("amenity", "arts_centre"): "Arts/Studios/Event Spaces",
    ("amenity", "studio"): "Arts/Studios/Event Spaces",
    ("tourism", "artwork"): "Arts/Studios/Event Spaces",
    ("amenity", "restaurant"): "Dining",
    ("amenity", "fast_food"): "Dining",
    ("amenity", "food_court"): "Dining",
    ("amenity", "cafe"): "Coffee/Bakery",
    ("shop", "bakery"): "Coffee/Bakery",
    ("shop", "coffee"): "Coffee/Bakery",
    ("amenity", "bar"): "Bars/Nightlife",
    ("amenity", "pub"): "Bars/Nightlife",
    ("amenity", "nightclub"): "Bars/Nightlife",
    ("amenity", "biergarten"): "Bars/Nightlife",
    ("leisure", "park"): "Parks/Outdoors",
    ("leisure", "garden"): "Parks/Outdoors",
    ("leisure", "nature_reserve"): "Parks/Outdoors",
    ("boundary", "national_park"): "Parks/Outdoors",
}

# category-only fallback (osm_category, None) -> our category
OSM_CATEGORY_MAP = {
    "shop": "Shops/Retail",
    "natural": "Parks/Outdoors",
}

# Substring (lowercased) -> category. Checked in order; first match wins.
KEYWORD_MAP = [
    ("gallery", "Galleries"),
    ("museum", "Museums/Cultural Institutions"),
    ("cultural center", "Museums/Cultural Institutions"),
    ("cultural centre", "Museums/Cultural Institutions"),
    ("studio", "Arts/Studios/Event Spaces"),
    ("atelier", "Arts/Studios/Event Spaces"),
    ("collective", "Arts/Studios/Event Spaces"),
    ("coffee", "Coffee/Bakery"),
    ("cafe", "Coffee/Bakery"),
    ("café", "Coffee/Bakery"),
    ("bakery", "Coffee/Bakery"),
    ("patisserie", "Coffee/Bakery"),
    ("cocktail", "Bars/Nightlife"),
    ("speakeasy", "Bars/Nightlife"),
    ("lounge", "Bars/Nightlife"),
    ("nightclub", "Bars/Nightlife"),
    (" bar", "Bars/Nightlife"),
    ("pub", "Bars/Nightlife"),
    ("pizzeria", "Dining"),
    ("trattoria", "Dining"),
    ("bistro", "Dining"),
    ("restaurant", "Dining"),
    ("eatery", "Dining"),
    ("park", "Parks/Outdoors"),
    ("garden", "Parks/Outdoors"),
]


def _load_overrides(overrides_path: str) -> dict:
    if not os.path.exists(overrides_path):
        return {}
    with open(overrides_path, "r", encoding="utf-8") as f:
        return json.load(f)


def categorize(title: str, tags: str, osm_category: str | None, osm_type: str | None,
                overrides_path: str = "data/category_overrides.json") -> tuple[str, str]:
    """Returns (category, confidence). confidence is one of:
    "override", "osm", "keyword", "none".
    """
    overrides = _load_overrides(overrides_path)
    if title in overrides:
        return overrides[title], "override"

    if osm_category and osm_type:
        mapped = OSM_TAG_MAP.get((osm_category, osm_type))
        if mapped:
            return mapped, "osm"

    haystack = f"{title} {tags or ''}".lower()
    for needle, category in KEYWORD_MAP:
        if needle in haystack:
            return category, "keyword"

    if osm_category:
        mapped = OSM_CATEGORY_MAP.get(osm_category)
        if mapped:
            return mapped, "osm"

    return "Other/Uncategorized", "none"
