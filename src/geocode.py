#!/usr/bin/env python3
"""Geocode a Takeout "Saved places" CSV via Nominatim, tracking progress so
reruns only touch new or failed rows.

Usage:
    python3 src/geocode.py <location> <csv_path> [--retry-failed]

`location` picks the data/<location>/ directory (state, category overrides,
config.json with the Nominatim query suffix + bounding box for that city).
See data/new_york/ for an example when adding a new city.

Safe to interrupt: state is saved after every row. Safe to rerun against the
same or a newer export of the same list - already-succeeded rows (keyed by
Google Maps URL) are skipped.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import paths
from lib import state as state_lib
from lib import categorize
from lib.nominatim import search, GeocodeError


def _pick(address: dict, *keys: str) -> str | None:
    for k in keys:
        if address.get(k):
            return address[k]
    return None


def _format_address(result: dict) -> str:
    addr = result.get("address", {})
    house = addr.get("house_number")
    road = addr.get("road")
    city = addr.get("city") or addr.get("town") or addr.get("village")
    state = addr.get("state")
    postcode = addr.get("postcode")

    if road:
        street = f"{house} {road}".strip() if house else road
        parts = [p for p in [street, city, state, postcode] if p]
        if parts:
            return ", ".join(parts)
    return result.get("display_name", "")


def _neighborhood(result: dict) -> str:
    addr = result.get("address", {})
    return _pick(addr, "neighbourhood", "quarter", "suburb", "city_district", "city") or ""


# addresstype values that indicate we matched an actual named venue rather
# than a generic street/place (e.g. "EDEN" drifting to "Mount Eden Avenue").
HIGH_CONFIDENCE_ADDRESSTYPES = {
    "tourism", "amenity", "shop", "leisure", "building", "office", "craft",
}


def _match_confidence(result: dict) -> str:
    return "high" if result.get("addresstype") in HIGH_CONFIDENCE_ADDRESSTYPES else "low"


def read_rows(csv_path: str) -> list[dict]:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("Title") or "").strip()
            url = (row.get("URL") or "").strip()
            if not title and not url:
                continue  # blank row
            rows.append(row)
    return rows


def geocode_one(title: str, query_suffix: str, viewbox: str | None) -> tuple[dict | None, str | None]:
    """Try a couple of query variants. Returns (result, error)."""
    queries = [f"{title}, {query_suffix}", title]
    last_error = None
    for q in queries:
        try:
            results = search(q, viewbox=viewbox)
        except GeocodeError as exc:
            last_error = str(exc)
            continue
        if results:
            return results[0], None
    return None, last_error or "no results"


def load_config(location: str) -> dict:
    path = paths.config_path(location)
    if not os.path.exists(path):
        raise SystemExit(
            f"No config at {path}. Add one with query_suffix and viewbox - "
            f"see data/new_york/config.json for an example."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("location", help="Location key, e.g. new_york (see data/<location>/)")
    parser.add_argument("csv_path", help="Path to the Takeout Saved-places CSV")
    parser.add_argument(
        "--retry-failed", action="store_true",
        help="Also retry rows previously marked failed (up to 3 attempts total)",
    )
    args = parser.parse_args()

    config = load_config(args.location)
    state_path = paths.state_path(args.location)
    overrides_path = paths.overrides_path(args.location)

    rows = read_rows(args.csv_path)
    state = state_lib.load(state_path)

    to_process = []
    for row in rows:
        title = row["Title"].strip()
        url = (row.get("URL") or "").strip()
        key = state_lib.key_for(title, url)
        if state_lib.should_process(state.get(key), args.retry_failed):
            to_process.append((key, row))

    print(f"{len(rows)} rows in input, {len(to_process)} to geocode "
          f"({len(rows) - len(to_process)} already done).")

    if not to_process:
        print("Nothing to do.")
        return

    for i, (key, row) in enumerate(to_process, 1):
        title = row["Title"].strip()
        url = (row.get("URL") or "").strip()
        tags = (row.get("Tags") or "").strip()
        print(f"[{i}/{len(to_process)}] {title}", end=" ... ", flush=True)

        record = state.get(key, {
            "title": title, "url": url, "tags": tags, "attempts": 0,
        })
        record["attempts"] = record.get("attempts", 0) + 1
        record["last_attempt"] = datetime.now(timezone.utc).isoformat()

        result, error = geocode_one(title, config["query_suffix"], config.get("viewbox"))
        if result is None:
            record["status"] = "failed"
            record["error"] = error
            print(f"FAILED ({error})")
        else:
            osm_category = result.get("category")
            osm_type = result.get("type")
            category, confidence = categorize.categorize(
                title, tags, osm_category, osm_type, overrides_path=overrides_path,
            )
            match_confidence = _match_confidence(result)
            record.update({
                "status": "success",
                "error": None,
                "lat": result.get("lat"),
                "lon": result.get("lon"),
                "address": _format_address(result),
                "neighborhood": _neighborhood(result),
                "display_name": result.get("display_name"),
                "osm_category": osm_category,
                "osm_type": osm_type,
                "category": category,
                "category_confidence": confidence,
                "match_confidence": match_confidence,
            })
            flag = "" if match_confidence == "high" else "  [LOW MATCH CONFIDENCE - verify]"
            print(f"OK -> {record['address']} [{category}/{confidence}]{flag}")

        state[key] = record
        state_lib.save(state, state_path)

    succeeded = sum(1 for r in state.values() if r.get("status") == "success")
    failed = sum(1 for r in state.values() if r.get("status") == "failed")
    print(f"\nDone. State totals: {succeeded} succeeded, {failed} failed "
          f"(of {len(state)} tracked places).")
    if failed:
        print("Failed titles:")
        for r in state.values():
            if r.get("status") == "failed":
                print(f"  - {r['title']} ({r.get('error')})")


if __name__ == "__main__":
    main()
