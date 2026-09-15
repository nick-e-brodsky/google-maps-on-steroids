#!/usr/bin/env python3
"""Build a My-Maps-ready CSV from a location's data/<location>/state.json.

Writes data/<location>/output/places.csv with a Category column. Import it
into Google My Maps as a single layer, then use "Style by data column" ->
Category to get per-category colors/icons with toggleable groups in the
map's legend - no need for separate per-category files.

Category is recomputed from the stored OSM tags + the location's
category_overrides.json on every run, so editing overrides doesn't require
re-geocoding.

Usage:
    python3 src/export.py <location>
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import paths
from lib import state as state_lib
from lib import categorize

FIELDS = ["Title", "Category", "Neighborhood", "Cuisine", "Address", "Lat", "Long", "Original_URL"]


def load_cuisine(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("location", help="Location key, e.g. new_york (see data/<location>/)")
    args = parser.parse_args()

    state_path = paths.state_path(args.location)
    overrides_path = paths.overrides_path(args.location)
    output_path = paths.output_path(args.location)
    cuisine = load_cuisine(paths.cuisine_path(args.location))

    state = state_lib.load(state_path)
    if not state:
        print(f"No state found at {state_path} - run src/geocode.py first.")
        return

    rows = []
    category_counts = {}
    confidence_counts = {}
    low_match_confidence = []
    failed = []

    for record in state.values():
        title = record["title"]
        if record.get("status") != "success":
            failed.append(record)
            continue

        category, confidence = categorize.categorize(
            title, record.get("tags", ""),
            record.get("osm_category"), record.get("osm_type"),
            overrides_path=overrides_path,
        )
        category_counts[category] = category_counts.get(category, 0) + 1
        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        if record.get("match_confidence") == "low":
            low_match_confidence.append(title)

        rows.append({
            "Title": title,
            "Category": category,
            "Neighborhood": record.get("neighborhood", ""),
            "Cuisine": cuisine.get(title, ""),
            "Address": record.get("address", ""),
            "Lat": record.get("lat", ""),
            "Long": record.get("lon", ""),
            "Original_URL": record.get("url", ""),
        })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {output_path} ({len(rows)} rows).")
    print(f"\n{len(state)} tracked, {len(rows)} succeeded, {len(failed)} failed.")
    print("By category:")
    for category, count in sorted(category_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {category}: {count}")
    print(f"Category confidence: {confidence_counts}")

    if failed:
        print("\nFailed to geocode (review or rerun with --retry-failed):")
        for r in failed:
            print(f"  - {r['title']} ({r.get('error')}, {r.get('attempts', 0)} attempts)")

    none_conf = confidence_counts.get("none", 0)
    if none_conf:
        print(f"\n{none_conf} place(s) fell back to Other/Uncategorized with no "
              f"OSM/keyword signal - worth a manual look via {overrides_path}.")

    if low_match_confidence:
        print(f"\n{len(low_match_confidence)} place(s) matched a generic street/area "
              f"rather than a specific venue - verify these manually:")
        for title in low_match_confidence:
            print(f"  - {title}")

    missing_cuisine = [r["Title"] for r in rows if r["Category"] == "Dining" and not r["Cuisine"]]
    if missing_cuisine:
        print(f"\n{len(missing_cuisine)} Dining place(s) missing cuisine - add to "
              f"{paths.cuisine_path(args.location)}:")
        for title in missing_cuisine:
            print(f"  - {title}")


if __name__ == "__main__":
    main()
