# Handoff — 2026-09-15

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

## The blocker to fix first

**10 of the 18 test places (56%) fail to geocode via Nominatim.** That's the
literal reason this session ended and the next one exists — Nick called it a
likely dealbreaker before any new features.

Important context `decisions/0002` doesn't fully capture: that ADR accepted
Nominatim's weak coverage *because the plan at the time was for Google My
Maps to do its own (much better) geocoding from Title at CSV-import time* —
Nominatim's coordinates wouldn't even be needed. Since then, the project
has shifted to the self-hosted Leaflet map above as the actual day-to-day
surface. **Leaflet has no geocoding of its own — it only draws a pin at
coordinates it's handed.** So the destination-does-its-own-geocoding escape
hatch doesn't apply here, and the Nominatim gap is a real, unresolved
problem for the surface actually being used, not a moot point.

`decisions/0002` already names the fallback that was deferred: the **Google
Geocoding API**. Nick was walked through key setup (Cloud Console project,
enable Geocoding API, billing, restrict the key to that API only) earlier
in the prior session, but **it's unconfirmed whether a key actually exists
yet** — ask him before assuming.

## Next task

1. Confirm whether Nick has a Google Geocoding API key. If not, the setup
   steps were already given once — regenerate them if needed rather than
   assuming he remembers.
2. Wire it in as a fallback (try Nominatim first since it's free; fall back
   to Google for anything Nominatim misses) — ask Nick if he'd rather
   replace Nominatim outright instead. Keep the key out of git (local
   env var / gitignored file), obviously.
3. Re-run against the 18-place test list and confirm the failure rate
   actually drops before treating this as solved — don't just assume the
   integration works.
4. Update `decisions/0002` to reflect the real outcome (it currently
   documents this as deferred/open).
5. Only after that: ask Nick for the full 150+ place list.

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
