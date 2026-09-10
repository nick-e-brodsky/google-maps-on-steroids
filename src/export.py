#!/usr/bin/env python3
"""Build My-Maps-ready CSVs from data/state.json.

Writes:
  data/output/all_places.csv               - every tracked place, incl. failures
  data/output/by_category/<Category>.csv   - one file per category, successes only
                                              (import each as a separate My Maps layer)

Category is recomputed from the stored OSM tags + data/category_overrides.json
on every run, so editing overrides doesn't require re-geocoding.

Usage:
    python3 src/export.py
"""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import state as state_lib
from lib import categorize

OUTPUT_DIR = "data/output"
FIELDS = ["Title", "Category", "Neighborhood", "Address", "Lat", "Long", "Original_URL"]


def safe_filename(category: str) -> str:
    return category.replace("/", "-") + ".csv"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default=state_lib.DEFAULT_STATE_PATH)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args()

    state = state_lib.load(args.state)
    if not state:
        print(f"No state found at {args.state} - run src/geocode.py first.")
        return

    by_category_dir = os.path.join(args.output_dir, "by_category")
    os.makedirs(by_category_dir, exist_ok=True)

    all_rows = []
    by_category = {}
    confidence_counts = {}
    low_match_confidence = []
    failed = []

    for record in state.values():
        title = record["title"]
        if record.get("status") != "success":
            failed.append(record)
            all_rows.append({
                "Title": title, "Category": "", "Neighborhood": "",
                "Address": "", "Lat": "", "Long": "",
                "Original_URL": record.get("url", ""),
            })
            continue

        category, confidence = categorize.categorize(
            title, record.get("tags", ""),
            record.get("osm_category"), record.get("osm_type"),
        )
        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        if record.get("match_confidence") == "low":
            low_match_confidence.append(title)

        row = {
            "Title": title,
            "Category": category,
            "Neighborhood": record.get("neighborhood", ""),
            "Address": record.get("address", ""),
            "Lat": record.get("lat", ""),
            "Long": record.get("lon", ""),
            "Original_URL": record.get("url", ""),
        }
        all_rows.append(row)
        by_category.setdefault(category, []).append(row)

    all_path = os.path.join(args.output_dir, "all_places.csv")
    with open(all_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    for category, rows in by_category.items():
        path = os.path.join(by_category_dir, safe_filename(category))
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    print(f"Wrote {all_path} ({len(all_rows)} rows).")
    print(f"Wrote {len(by_category)} category files under {by_category_dir}/:")
    for category in sorted(by_category, key=lambda c: -len(by_category[c])):
        print(f"  {category}: {len(by_category[category])}")

    print(f"\n{len(state)} tracked, {len(all_rows) - len(failed)} succeeded, "
          f"{len(failed)} failed.")
    print(f"Category confidence: {confidence_counts}")
    if failed:
        print("\nFailed to geocode (review or rerun with --retry-failed):")
        for r in failed:
            print(f"  - {r['title']} ({r.get('error')}, {r.get('attempts', 0)} attempts)")

    none_conf = confidence_counts.get("none", 0)
    if none_conf:
        print(f"\n{none_conf} place(s) fell back to Other/Uncategorized with no "
              f"OSM/keyword signal - worth a manual look via data/category_overrides.json.")

    if low_match_confidence:
        print(f"\n{len(low_match_confidence)} place(s) matched a generic street/area "
              f"rather than a specific venue - verify these manually:")
        for title in low_match_confidence:
            print(f"  - {title}")


if __name__ == "__main__":
    main()
