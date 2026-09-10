# google-maps-on-steroids

Turns a Google Takeout "Saved places" CSV export into categorized,
geocoded CSVs ready to import into Google My Maps as per-category layers.

## Pipeline

```
python3 -m pip install -r requirements.txt

# 1. Export a Google Maps saved list via Google Takeout ("Saved" export)
#    and drop the CSV into data/input/.

# 2. Geocode (resumable - safe to interrupt/rerun; only new/failed rows
#    are processed on subsequent runs).
python3 src/geocode.py data/input/<your_export>.csv

# 3. Build the My Maps import files.
python3 src/export.py
```

`src/export.py` writes:
- `data/output/all_places.csv` — every tracked place, including failures
- `data/output/by_category/<Category>.csv` — one file per category,
  successes only. Import each file into Google My Maps as a separate layer.

## Adding places later / re-running

Progress is tracked in `data/state.json`, keyed by each place's Google Maps
URL, and committed to the repo so it survives across sessions. To add newly
saved places:

1. Export an updated CSV from Takeout (it can be the full list again, or
   just new places — either works).
2. Run `python3 src/geocode.py data/input/<file>.csv` again. Already-succeeded
   places are skipped automatically; only new places hit the API.
3. Run `python3 src/export.py` to regenerate the output CSVs.

To retry places that failed to geocode (up to 3 attempts total per place):

```
python3 src/geocode.py data/input/<file>.csv --retry-failed
```

## Categories

Fixed, flat list (do not add new top-level categories without checking in
with Nick first):

1. Dining
2. Coffee/Bakery
3. Bars/Nightlife
4. Galleries
5. Museums/Cultural Institutions
6. Arts/Studios/Event Spaces (public art, murals, working studios,
   art-adjacent event spaces)
7. Shops/Retail
8. Parks/Outdoors
9. Other/Uncategorized (catch-all)

Category is assigned heuristically from OpenStreetMap tags on the matched
place, falling back to keyword matching on the title, falling back to
Other/Uncategorized. This is best-effort, not ground truth — check
`data/output/all_places.csv` and fix misclassifications via
`data/category_overrides.json` (a `{"Title": "Category"}` map — entries
here always win, and `src/export.py` re-applies overrides on every run
without re-geocoding).

## Geocoding source: Nominatim (OpenStreetMap)

Uses the free public Nominatim API — no key/account needed. Rate-limited to
~1 req/sec per Nominatim's usage policy, with retry/backoff on transient
failures (useful over flaky connections). Searches are bounded to a NYC
viewbox to avoid false-positive matches on same-named places elsewhere
(e.g. a business called "EDEN" matching a town upstate instead of the SoHo
gallery).

**Known limitation:** Nominatim's coverage of small/newer NYC businesses
(galleries, boutique studios, etc.) is noticeably weaker than Google's. On
an 18-place test batch, ~56% failed to geocode at all (no result found),
and one further match landed on a generic street name rather than the
actual venue (flagged in output as `match_confidence: low`). If this
failure rate holds on the full list, the documented fallback is the Google
Places API (requires generating an API key via Google Cloud Console — not
set up here, since it needs a separate conversation about credential
storage).

Failed and low-confidence matches are called out in `src/export.py`'s
summary output and left blank/flagged in `data/output/all_places.csv` for
manual fill-in rather than guessed at.

## Known data quirks

- Don't deduplicate. Similarly-named entries (e.g. "EDEN" vs.
  "EDEN (Eden Gallery) - SoHo") may be genuinely separate saves, and
  multiple branches of the same business are expected. Every row is
  geocoded independently.
- Titles aren't always self-explanatory business names — don't assume
  category/neighborhood from a place's position in the list.
- Studio buildings / multi-tenant art spaces (e.g. "56 Bogart St") often
  have no matching OSM business tag and fall back to
  Other/Uncategorized — use `data/category_overrides.json` to fix these.
