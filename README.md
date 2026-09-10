# google-maps-on-steroids

Turns a Google Takeout "Saved places" CSV export into a categorized, geocoded
CSV ready to import into Google My Maps, with per-category styling.

## Repo layout

Each Google Maps saved list (New York, Paris, Tokyo, ...) is self-contained
under `data/<location>/`:

```
data/<location>/
  config.json               # Nominatim query suffix + bounding box for this city
  category_overrides.json   # manual {"Title": "Category"} corrections
  input/                    # Takeout CSV export(s) go here
  state.json                # progress tracking (committed - survives across sessions)
  output/places.csv         # final My Maps import file
```

## Pipeline

```
python3 -m pip install -r requirements.txt

# 1. Export a Google Maps saved list via Google Takeout ("Saved" export)
#    and drop the CSV into data/<location>/input/.

# 2. Geocode (resumable - safe to interrupt/rerun; only new/failed rows
#    are processed on subsequent runs).
python3 src/geocode.py <location> data/<location>/input/<file>.csv

# 3. Build the My Maps import file.
python3 src/export.py <location>
```

`src/export.py` writes `data/<location>/output/places.csv` — import it into
Google My Maps as a single layer, then use **Style by data column ->
Category** to get per-category colors/icons with toggleable groups in the
map's legend. One file, one layer, filterable by category in the UI — no
need for separate per-category files.

## Adding a new city

1. Create `data/<city>/` with `input/` and a `config.json`:
   ```json
   {
     "query_suffix": "Paris, France",
     "viewbox": "left,top,right,bottom"
   }
   ```
   (`viewbox` bounds Nominatim matches to the city so same-named places
   elsewhere don't get matched by mistake — see `data/new_york/config.json`
   for a real example, or look up a bounding box for the city.)
2. Drop the Takeout CSV into `data/<city>/input/`.
3. Run the pipeline with `<city>` as the location argument.

## Adding places later / re-running

Progress is tracked in `data/<location>/state.json`, keyed by each place's
Google Maps URL, and committed to the repo so it survives across sessions.
To add newly saved places:

1. Export an updated CSV from Takeout (it can be the full list again, or
   just new places — either works).
2. Run `python3 src/geocode.py <location> data/<location>/input/<file>.csv`
   again. Already-succeeded places are skipped automatically; only new
   places hit the API.
3. Run `python3 src/export.py <location>` to regenerate `places.csv`.

To retry places that failed to geocode (up to 3 attempts total per place):

```
python3 src/geocode.py <location> data/<location>/input/<file>.csv --retry-failed
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
`data/<location>/output/places.csv` and fix misclassifications via
`data/<location>/category_overrides.json` (a `{"Title": "Category"}` map —
entries here always win, and `src/export.py` re-applies overrides on every
run without re-geocoding).

## Geocoding source: Nominatim (OpenStreetMap)

Uses the free public Nominatim API — no key/account needed. Rate-limited to
~1 req/sec per Nominatim's usage policy, with retry/backoff on transient
failures (useful over flaky connections). Searches are bounded to each
location's `viewbox` to avoid false-positive matches on same-named places
elsewhere (e.g. a business called "EDEN" matching a town upstate instead of
the SoHo gallery).

**Known limitation:** Nominatim's coverage of small/newer businesses
(galleries, boutique studios, etc.) is noticeably weaker than Google's. On
an 18-place NYC test batch, ~56% failed to geocode at all (no result found),
and one further match landed on a generic street name rather than the
actual venue (flagged in output as `match_confidence: low`). If this
failure rate holds on the full list, the documented fallback is the Google
Places API (requires generating an API key via Google Cloud Console — not
set up here, since it needs a separate conversation about credential
storage).

Failed and low-confidence matches are called out in `src/export.py`'s
summary output and left out of `places.csv` (failures) or flagged in the
summary (low-confidence matches) for manual review rather than guessed at.

## Known data quirks

- Don't deduplicate. Similarly-named entries (e.g. "EDEN" vs.
  "EDEN (Eden Gallery) - SoHo") may be genuinely separate saves, and
  multiple branches of the same business are expected. Every row is
  geocoded independently.
- Titles aren't always self-explanatory business names — don't assume
  category/neighborhood from a place's position in the list.
- Studio buildings / multi-tenant art spaces (e.g. "56 Bogart St") often
  have no matching OSM business tag and fall back to
  Other/Uncategorized — use `data/<location>/category_overrides.json` to
  fix these.

## Working notes

- Free to merge my own PRs without waiting on review — keep CI light/nonexistent
  and avoid burning tokens or bloating the repo with generated cruft.
- "Automatically delete head branches" is on, so merged branches clean
  themselves up.
