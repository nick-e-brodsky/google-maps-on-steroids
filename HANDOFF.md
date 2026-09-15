# Handoff — 2026-09-15 (updated)

Session-to-session continuity note. Read this first, then `README.md` (pipeline
usage) and `decisions/` (why things are built this way — start with the index
at `decisions/README.md`). `AGENTS.md` has the working conventions (branching,
self-merge, token economy, etc.) — follow them without being reminded.

## Where things stand

- Pipeline (`src/geocode.py`, `src/export.py`, `src/lib/`) geocodes a Takeout
  saved-places CSV via Nominatim (OpenStreetMap), assigns category/neighborhood,
  writes `data/<location>/output/places.csv`.
- Only `new_york` exists so far, and only the 18-place **test** list has been
  run (data/new_york/input/test_ny_list.csv) — the real 150+ place list hasn't
  been sent yet. **Do not run against the full list until the geocoding
  problem below is actually fixed** — no point re-running a broken pipeline
  at 10x the size.
- `prototypes/leaflet_map/` has become the real, actively-used surface — not
  just a throwaway prototype anymore. It's hosted live via GitHub Pages:
  **https://nick-e-brodsky.github.io/google-maps-on-steroids/**
  (auto-deploys ~1-2 min after any push to `main`). Filterable by
  category/neighborhood/cuisine, shows a place count, links each pin to
  Google Maps. The repo is **public** (decisions/0004) — that was a
  deliberate, explicit tradeoff Nick chose after comparing alternatives;
  don't re-litigate it without him raising it.

## The blocker that was fixed this session

**Was:** 10 of 18 test places (56%) failed to geocode via Nominatim alone —
a real problem for the Leaflet map (the actual day-to-day surface), which
has no geocoding of its own and just draws pins at coordinates it's handed.

**Fix:** added the Google Geocoding API as a fallback (`src/lib/
google_geocode.py`) — Nominatim tried first (free), Google only called for
what it misses. Nick already had a key set up from a prior session. Re-ran
the 18-place test list with the fallback: **0/18 failures now** (all 10
previously-failed places resolved at high match confidence via Google).
See `decisions/0005` for the full writeup; `decisions/0002` is superseded.

One pre-existing low-confidence match remains (bare "EDEN" title matching
a Bronx street) — that's a title-ambiguity issue, not a coverage gap, so
the fallback doesn't and shouldn't fix it. Flagged as before for manual
review.

## Next task

Ask Nick for the full 150+ place list and run the now-fixed pipeline
against it. Watch for:
- Whether the 0% failure rate on 18 places holds at scale (more
  small/newer businesses could still slip past both providers).
- Google API cost — should stay near-zero since it's a fallback, but worth
  a sanity check with `source` counts in `state.json` after a full run.

## Loose ends (not urgent, don't chase unless asked)

- One stale branch, `claude/maps-geolocation-batch-bxh85y`, predates
  "automatically delete head branches" being enabled and can't be deleted
  with the GitHub tools available in this environment (no repo-settings/
  branch-delete endpoint exposed) — cosmetic, safe to ignore or delete
  manually on github.com.
- Nick works from an iPad. Two dead ends worth knowing about if a similar
  need comes up: iOS Quick Look previews block external network requests
  entirely (so a local HTML file with CDN/tile dependencies renders blank),
  and mobile Safari will silently try to upgrade a typed `http://` local-
  network URL to `https://` (breaks against a plain `python3 -m http.server`
  test server) unless the address bar explicitly shows `http://`.
