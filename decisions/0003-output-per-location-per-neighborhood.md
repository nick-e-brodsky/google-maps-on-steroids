# 0003: Output organized per-location, split by neighborhood

Status: Accepted (structure); implementation pending on 0002's open question
Date: 2026-09-11

## Context

The project will expand beyond New York to other cities (Paris, Tokyo,
...). Within a city, the original use case is neighborhood-scoped
("show me galleries in Bushwick" while out with friends), and Google My
Maps supports styling/grouping a single imported layer by a data column
(e.g. Category) but each layer is still one imported file.

## Decision

- Each location gets its own directory: `data/<location>/`.
- Within a location, output is a combined `places.csv` (whole location,
  all neighborhoods - source of truth / reference) plus a per-neighborhood
  split (`output/by_neighborhood/<Neighborhood>.csv`) for import as
  separate My Maps layers, each styled by Category internally.
- This does not include a separate per-category split - that was tried
  and dropped (redundant with per-column styling inside a single layer).

## Alternatives considered

- Per-category split instead of per-neighborhood: dropped earlier
  (redundant with My Maps' native "style by column").
- Single combined file only: doesn't give neighborhood-scoped layers,
  which is the primary way Nick expects to use the map day-to-day.

## Consequences

- Exact output columns depend on 0002's open question (which map tool):
  if My Maps stays the target, Lat/Long/Address drop out of the required
  columns since My Maps geocodes from Title itself.
- Not yet implemented in `src/export.py` - waiting on 0002.
