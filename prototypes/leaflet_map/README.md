# Leaflet map prototype

Exploratory - evaluating a custom map as an alternative to Google My Maps
(see `decisions/0002-geocode-via-destination-tool.md`, still open).

```
python3 prototypes/leaflet_map/build_map.py <location>
```

Reads `data/<location>/state.json`, plots every successfully-geocoded place
as a colored marker (by Category) on OpenStreetMap tiles via Leaflet, writes
a self-contained `<location>.html`.

Open the output file directly in a browser - do not publish it as a Claude
Artifact. Artifacts sandbox blocks image/tile requests to hosts outside a
small CDN allowlist, so the OpenStreetMap basemap tiles would silently fail
to load there.

Currently only plots Nominatim-geocoded places (the ones with lat/long
already resolved). A Google Geocoding API comparison is the natural next
step once a key is available - would add a second marker set/toggle to
compare coverage and placement against Nominatim on the same test list.
