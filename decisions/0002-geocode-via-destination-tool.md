# 0002: Geocode via the destination map tool, not a pre-resolved Nominatim pipeline

Status: Accepted (direction); which destination tool is still open, see below
Date: 2026-09-11

## Context

`src/geocode.py` originally pre-resolved lat/long via the free Nominatim
(OpenStreetMap) API before any map import. On an 18-place NYC test batch,
Nominatim failed to find ~56% of places (small/newer businesses have weak
OSM coverage) and one further match was a false positive (a business
called "EDEN" nearly matched a street in the Bronx).

Testing Google My Maps' own CSV import directly against the `Title` column
resolved most of the same places successfully - it's backed by the same
underlying data as the original Google Maps Saved list, for free, with no
API key. The only unresolved case ("EDEN") is rare enough to fix manually
(look it up, fill in coordinates by hand).

## Decision

Stop pre-resolving coordinates ourselves for the primary path. Let the
destination map tool geocode from `Title` (or `Original_URL`) at import
time, when the tool supports it well.

This is conditional on which map tool we standardize on (My Maps has no
public API for import - see the open question below). If we later adopt a
tool that needs coordinates supplied directly (e.g. a custom Leaflet/Mapbox
map), this decision is revisited and the Nominatim pipeline may come back.

## Alternatives considered

- Keep Nominatim, accept the ~56% manual-fill-in rate.
- Google Places/Geocoding API as a fallback for Nominatim failures.
  Deferred: needs an API key and a credential-storage conversation; moot
  if the destination tool geocodes well enough on its own.

## Consequences

- `src/geocode.py` and `src/lib/nominatim.py` are **deprecated but not
  deleted from the working tree yet** - kept until the map-tool choice
  below is settled, since they'd be needed again for a coordinates-based
  tool. (Once removed, they remain recoverable from git history regardless.)
- Output no longer needs Lat/Long/Address as required fields for the
  Google My Maps path.
- **Open question, not yet decided:** which map tool to standardize on.
  Google My Maps has no public API for programmatic import (confirmed via
  web search, Sept 2026) - CSV import is a manual step, layers cap at
  ~2,000 rows, and an imported layer does not live-sync with the source
  file. It does, however, live in the same Google Maps app already used
  daily on mobile, which matches this project's original "show me
  galleries in Bushwick, out with friends" use case. Alternatives
  (Mapbox, Leaflet-based custom map, Pin Drop, Mapme, MapHub) either
  require a different app than the one already on Nick's phone, reintroduce
  the geocoding-quality problem, or both. No alternative found that
  combines free high-quality geocoding, a true API, and the native phone
  Maps app. Revisit if manual CSV upload becomes too painful at scale.
