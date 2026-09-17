# 0007: Exclude far-flung places from the initial map fit using the existing viewbox

Status: Accepted
Date: 2026-09-17

## Context

Issue #23: with the full 450-place NY list plotted (#22), a handful of
legitimately-geocoded but geographically distant places (Watkins Glen
State Park, Dia Beacon, MANITOGA, James Rose Center, plus a couple of
other upstate spots) skewed `refresh()`'s naive `map.fitBounds(bounds)`
call so far out that it had to zoom to a whole-state view, collapsing
~440 tightly-packed NYC markers into a single `leaflet.markercluster`
blob on load.

## Decision

`build_map.py` already loads each location's `config.json`, which
carries a `viewbox` (`left,top,right,bottom`) used to bias Nominatim
geocoding toward the city. Reuse that same box: pass it into the
generated HTML as `coreBbox`, and in `refresh()`, compute the initial
`fitBounds` call from only the visible markers that fall inside it,
falling back to all visible markers if none do (e.g. a filter combo that
happens to show only outliers). Markers outside the box are still added
to the cluster layer and rendered normally - just excluded from the
bounds calculation - so they stay reachable by panning/zooming out
manually.

Checked against the real NY dataset: the NYC viewbox
(`-74.26,40.92,-73.68,40.48`) cleanly separates the 6 actual outliers
(all >30km from the metro core) from every in-city place (all <28km),
including borderline ones like The Met Cloisters and Isle of Us that a
naive distance/statistical cutoff would risk misclassifying.

## Alternatives considered

- Statistical outlier exclusion (median/IQR/MAD distance from a computed
  center). Tried this first empirically against the real dataset - every
  fixed multiplier either pulled in legitimate outer-borough places
  (Isle of Us, SILO, 929) or let a real outlier (James Rose Center, just
  outside the NYC border in Ridgewood, NJ) through, because the "gap"
  between legitimate far-borough places and actual day-trip outliers is
  only a few km. The viewbox is already a human-curated boundary for
  exactly this city, so it's both simpler and more accurate than fitting
  a statistical threshold with no natural separation in the data.
- Cap `fitBounds`'s zoom via its `maxZoom` option. Doesn't work: Leaflet's
  `maxZoom` only limits zooming *in*, not *out*, so it wouldn't have
  helped in the direction this bug goes. Also, even a manually clamped
  zoom would still center on the full bounding box's centroid (which
  landed near the Pennsylvania border with the outliers included) rather
  than the actual dense cluster, so it would show the wrong area anyway.

## Consequences

- No new per-city config needed - every location that already has a
  `config.json` viewbox gets this for free; a location without one (or
  without a `viewbox` key) falls back to the old whole-bounds behavior.
- The exclusion applies on every `refresh()` (not just initial load), so
  filtering down to a small set of in-city places also fits tightly
  rather than staying zoomed out because an outlier happens to still be
  checked in some filter group.
