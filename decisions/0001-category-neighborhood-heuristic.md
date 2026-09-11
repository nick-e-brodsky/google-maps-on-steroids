# 0001: Category & neighborhood via lightweight heuristic, not an external API

Status: Accepted
Date: 2026-09-11

## Context

Each place needs a Category (from a fixed list) and a Neighborhood. The
original design pulled these from Nominatim's OSM tags/address breakdown
automatically. Dropping Nominatim as the geocoding source (see 0002) means
that automatic signal goes away.

The data volume here is small (currently 18 test places, expected to reach
a few hundred across all locations) - not the scale that justifies a more
complex or fragile pipeline (e.g. calling an LLM or paid API per row on a
fixed schedule).

## Decision

Keep category/neighborhood assignment as: a fast keyword-matching pass
(`src/lib/categorize.py`) for the obvious cases, with Claude reasoning
directly about ambiguous ones (and web-searching when genuinely unclear,
as with "Moonzescope" in the original handoff) rather than building an
automated API-based classifier. `category_overrides.json` remains the
escape hatch for corrections.

## Alternatives considered

- Google Places API (or another places/POI API) to fetch category +
  neighborhood automatically. Rejected for now: adds a paid API and a
  credential-storage decision for a problem the data volume doesn't
  require solving programmatically.

## Consequences

- No new API dependency for categorization.
- Costs more of Claude's/the agent's active involvement per place than a
  pure script would, in exchange for better accuracy on ambiguous titles.
- Revisit if token cost becomes disproportionate to the task as volume
  grows (e.g. many more cities/places at once).
