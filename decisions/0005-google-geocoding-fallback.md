# 0005: Add the Google Geocoding API as a fallback for Nominatim misses

Status: Accepted
Date: 2026-09-15

## Context

`decisions/0002` moved geocoding responsibility onto the destination map
tool (planned: Google My Maps importing from `Title` at CSV-import time),
accepting Nominatim's weak small-business coverage as moot since Nominatim's
coordinates wouldn't be needed.

Since then, the project's actual day-to-day surface became the self-hosted
Leaflet map (`prototypes/leaflet_map/`, live via GitHub Pages), not Google
My Maps. Leaflet has no geocoding of its own — it only draws a pin at
coordinates it's handed. So pre-resolved coordinates are required again,
and Nominatim's ~56% failure rate on the 18-place NYC test batch (see
0002) is a real, unresolved blocker for the surface actually in use.

## Decision

Keep Nominatim as the first attempt (free, no key), and add the Google
Geocoding API (`src/lib/google_geocode.py`) as a fallback for whatever
Nominatim can't find, rather than replacing Nominatim outright. This
minimizes paid API calls to only the places that need them.

Requires `GOOGLE_MAPS_API_KEY` in the environment (Nick already had a
Cloud Console project + key set up from a prior session). Never committed
to git.

Re-ran the 18-place NYC test batch with the fallback enabled: all 10
previously-failed places succeeded via Google, all at high match
confidence. Failure rate: 56% -> 0%.

## Alternatives considered

- Destination tool (Google My Maps) does its own geocoding from `Title` -
  0002's original plan. No longer applies: Leaflet is the actual surface,
  and it needs coordinates handed to it directly.
- Replace Nominatim outright with Google. Rejected for now: Nominatim
  already resolves most places for free; only paying for the misses keeps
  API cost near-zero at this project's volume (~150 places).

## Consequences

- `src/geocode.py` and `src/lib/nominatim.py` are back in active use (no
  longer "deprecated but not deleted" per 0002).
- Every successful record now carries a `source` field (`nominatim` or
  `google`) in `state.json`, so it's visible which provider resolved each
  place.
- One remaining low-confidence match (bare "EDEN") is a title-ambiguity
  issue, not a coverage gap, so this fallback doesn't fix it - still
  flagged for manual review as before.
- Unblocks running the pipeline against the full 150+ place list, next.
