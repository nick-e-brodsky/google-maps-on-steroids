# Decisions

Lightweight architecture decision records (ADRs) for this project. One file
per decision, numbered in order.

Record a decision here whenever we choose one approach over real
alternatives for how the pipeline or data is structured (not routine
implementation details). See `AGENTS.md` at the repo root for the rule.

## Template

```markdown
# NNNN: Title

Status: Proposed | Accepted | Superseded by NNNN
Date: YYYY-MM-DD

## Context
What prompted this, what constraints applied.

## Decision
What we're doing.

## Alternatives considered
Briefly, what else we looked at and why not.

## Consequences
What this makes easier/harder, what it leaves open.
```

## Index

1. [Category & neighborhood via lightweight heuristic, not an external API](0001-category-neighborhood-heuristic.md)
2. [Geocode via the destination map tool, not a pre-resolved Nominatim pipeline](0002-geocode-via-destination-tool.md)
3. [Output organized per-location, split by neighborhood](0003-output-per-location-per-neighborhood.md)
4. [Make the repo public, host the map via GitHub Pages](0004-public-repo-github-pages.md)
5. [Add the Google Geocoding API as a fallback for Nominatim misses](0005-google-geocoding-fallback.md)
6. [Backfill neighborhood via Nominatim reverse geocode for Google-fallback places](0006-nominatim-reverse-backfill-for-google-neighborhood.md)
