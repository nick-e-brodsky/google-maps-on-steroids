# 0006: Backfill neighborhood via Nominatim reverse geocode for Google-fallback places

Status: Accepted
Date: 2026-09-17

## Context

`decisions/0005` added the Google Geocoding API as a fallback for places
Nominatim can't find by name, keyed off `_neighborhood()`'s use of
Nominatim's rich `neighbourhood`/`quarter`/`suburb` address tags (from
OSM's admin-boundary layer). Google's Geocoding API has no equivalent tag:
`to_nominatim_shape()` fell back to `locality` when `neighborhood`/
`sublocality` was absent, which for NYC addresses is frequently just the
borough (e.g. "Manhattan") — far coarser than what Nominatim-sourced
places get. In the 18-place NY test batch, 6 of the 10 Google-fallback
places ended up labeled "Manhattan", collapsing genuinely different
neighborhoods (SoHo, Tribeca, West Village, etc.) into one bucket and
making the map's neighborhood filter useless for them (issue #13).

## Decision

After Google resolves a place's lat/lon, do a free Nominatim **reverse**
geocode at those coordinates (`nominatim.reverse()`, new alongside the
existing `search()`, same rate-limit/retry client) and use its
`neighbourhood`/`quarter`/`suburb` tag (via the existing `_neighborhood()`
picker, for consistency with how Nominatim-sourced places are already
labeled) in place of Google's own locality guess. Google's lat/lon and
formatted address remain the source of truth — this only backfills the
neighborhood label. Best-effort: if the reverse lookup fails or returns
nothing, Google's original value is left in place rather than failing the
whole geocode.

## Alternatives considered

- Parse Google's `administrative_area_level_*`/`sublocality_level_*`
  components more aggressively. Rejected: Google's API just doesn't carry
  fine-grained neighborhood data for most of these addresses regardless of
  which component types are inspected — the underlying data isn't there.
- Hardcode a lat/lon-to-neighborhood lookup table for NYC. Rejected: brittle
  and doesn't generalize to future cities: reusing Nominatim's own
  comprehensive OSM boundary data via reverse geocoding is equally free and
  already scoped per-location by `config.json`.

## Consequences

- One extra free Nominatim request per Google-fallback place (still rate-
  limited to 1 req/sec by the shared client) - negligible at this
  project's volume.
- Google-fallback places can now get a neighborhood from a different
  source than their address/lat/lon (Google) - acceptable since Nominatim's
  OSM boundary layer is more granular than Google's locality tag, which is
  the whole point.
