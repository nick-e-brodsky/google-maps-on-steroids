#!/usr/bin/env python3
"""Prototype: render a location's geocoded places as a self-contained Leaflet
map (OpenStreetMap tiles), colored by category, filterable by category and
neighborhood.

Exploratory - part of evaluating the custom-map alternative to Google My
Maps (see decisions/0002-geocode-via-destination-tool.md). Not part of the
main pipeline; doesn't touch data/ or src/.

Usage:
    python3 prototypes/leaflet_map/build_map.py <location>

Output is a plain HTML file - open it directly in a browser (double-click,
or `open`/`xdg-open`). It is NOT meant to be published as a Claude Artifact:
Artifacts sandbox blocks image/tile requests to arbitrary hosts, so
OpenStreetMap's basemap tiles would silently fail to load there.
"""

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src")
sys.path.insert(0, _SRC)

from lib import paths
from lib import state as state_lib
from lib import categorize

CATEGORY_COLORS = {
    "Dining": "#e74c3c",
    "Coffee/Bakery": "#935116",
    "Bars/Nightlife": "#8e44ad",
    "Galleries": "#2980b9",
    "Museums/Cultural Institutions": "#16a085",
    "Arts/Studios/Event Spaces": "#d35400",
    "Shops/Retail": "#f1c40f",
    "Parks/Outdoors": "#27ae60",
    "Other/Uncategorized": "#7f8c8d",
}

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>{location} - Leaflet prototype</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<style>
  html, body {{ margin: 0; height: 100%; font-family: system-ui, sans-serif; }}
  #map {{ height: 100%; }}
  .filters {{
    background: white; padding: 10px 12px; border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3); font-size: 13px; line-height: 1.5;
    max-height: 60vh; overflow-y: auto; width: 220px; max-width: calc(100vw - 20px);
  }}
  .filters h4 {{ margin: 4px 0 4px; font-size: 12px; text-transform: uppercase;
    color: #555; display: flex; justify-content: space-between; align-items: center; }}
  .filters .toggle-all {{ font-size: 11px; font-weight: normal; text-transform: none;
    color: #2980b9; cursor: pointer; text-decoration: underline; }}
  .filters label {{ display: flex; align-items: center; gap: 6px; cursor: pointer; }}
  .filters .swatch {{
    display: inline-block; width: 10px; height: 10px; border-radius: 50%; flex: none;
  }}
  .filters hr {{ border: none; border-top: 1px solid #ddd; margin: 8px 0; }}
  .stats {{ font-size: 12px; color: #333; margin-bottom: 4px; }}
  .stats.failed {{ color: #888; margin-bottom: 8px; }}
  .popup-link {{ display: inline-block; margin-top: 4px; }}
  .filters-toggle {{ display: none; cursor: pointer; font-weight: 600; align-items: center;
    justify-content: space-between; gap: 8px; }}
  .filters-toggle .chevron {{ font-size: 10px; transition: transform 0.15s; }}
  @media (max-width: 600px) {{
    .filters-toggle {{ display: flex; }}
    .filters.collapsed {{ width: auto; max-height: none; }}
    .filters.collapsed .filters-body {{ display: none; }}
    .filters:not(.collapsed) .filters-toggle .chevron {{ transform: rotate(180deg); }}
    .filters:not(.collapsed) .filters-toggle {{ margin-bottom: 6px; }}
  }}
</style>
</head>
<body>
<div id="map"></div>
<script>
  const places = {places_json};
  const colors = {colors_json};
  const totalPlotted = {total_plotted};
  const failedCount = {failed_count};
  const coreBbox = {core_bbox_json};

  const categories = [...new Set(places.map(p => p.category))].sort();
  const neighborhoods = [...new Set(places.map(p => p.neighborhood).filter(Boolean))].sort();
  const cuisines = [...new Set(places.map(p => p.cuisine).filter(Boolean))].sort();

  const map = L.map('map');
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }}).addTo(map);

  const clusterGroup = L.markerClusterGroup();
  clusterGroup.addTo(map);

  const activeCategories = new Set(categories);
  const activeNeighborhoods = new Set(neighborhoods);
  const activeCuisines = new Set(cuisines);

  function escapeHtml(s) {{
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }}

  const markers = places.map(p => {{
    const color = colors[p.category] || '#333';
    const marker = L.circleMarker([p.lat, p.lon], {{
      radius: 7, color: color, fillColor: color, fillOpacity: 0.85, weight: 1,
    }});
    const cuisineLine = p.cuisine ? `<br>${{escapeHtml(p.cuisine)}} cuisine` : '';
    const mapsLink = p.url
      ? `<br><a class="popup-link" href="${{escapeHtml(p.url)}}" target="_blank" rel="noopener">View on Google Maps</a>`
      : '';
    marker.bindPopup(`<b>${{escapeHtml(p.title)}}</b><br>${{escapeHtml(p.category)}}${{cuisineLine}}<br>${{escapeHtml(p.neighborhood || '')}}${{mapsLink}}`);
    return {{ marker, place: p }};
  }});

  // Cuisine only applies to places that have one (Dining) - a place with no
  // cuisine value is never hidden by the cuisine filter.
  function applyFilters() {{
    const bounds = [];
    markers.forEach(({{ marker, place }}) => {{
      const visible = activeCategories.has(place.category) &&
        (place.neighborhood === '' || activeNeighborhoods.has(place.neighborhood)) &&
        (place.cuisine === '' || activeCuisines.has(place.cuisine));
      if (visible) {{
        if (!clusterGroup.hasLayer(marker)) clusterGroup.addLayer(marker);
        bounds.push([place.lat, place.lon]);
      }} else if (clusterGroup.hasLayer(marker)) {{
        clusterGroup.removeLayer(marker);
      }}
    }});
    return bounds;
  }}

  // A few legitimately-geocoded places (e.g. upstate day trips) sit far
  // outside the city proper; including them in fitBounds would zoom out
  // so far that the dense in-city markers collapse into one cluster. Fit
  // to the places inside the location's core viewbox when possible - the
  // rest stay plotted and reachable by panning/zooming out manually.
  function inCoreBbox([lat, lon]) {{
    if (!coreBbox) return true;
    return lon >= coreBbox.west && lon <= coreBbox.east &&
      lat >= coreBbox.south && lat <= coreBbox.north;
  }}

  function refresh() {{
    const bounds = applyFilters();
    const statsEl = document.getElementById('stats-count');
    if (statsEl) statsEl.textContent = `Showing ${{bounds.length}} of ${{totalPlotted}} places`;
    const coreBounds = bounds.filter(inCoreBbox);
    const fitTo = coreBounds.length ? coreBounds : bounds;
    if (fitTo.length) {{ map.fitBounds(fitTo, {{ padding: [30, 30] }}); }}
    else {{ map.setView([40.7128, -74.0060], 12); }}
  }}

  function buildFilterGroup(title, items, activeSet, colorFor) {{
    const div = L.DomUtil.create('div');
    const header = L.DomUtil.create('h4', '', div);
    header.innerHTML = `<span>${{title}}</span>`;
    const toggle = L.DomUtil.create('span', 'toggle-all', header);
    toggle.textContent = 'All / None';
    toggle.onclick = () => {{
      const allOn = items.every(i => activeSet.has(i));
      items.forEach(i => allOn ? activeSet.delete(i) : activeSet.add(i));
      div.querySelectorAll('input').forEach(cb => cb.checked = !allOn);
      refresh();
    }};
    items.forEach(item => {{
      const label = L.DomUtil.create('label', '', div);
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = true;
      cb.onchange = () => {{
        if (cb.checked) activeSet.add(item); else activeSet.delete(item);
        refresh();
      }};
      label.appendChild(cb);
      if (colorFor) {{
        const sw = L.DomUtil.create('span', 'swatch', label);
        sw.style.background = colorFor(item);
      }}
      label.appendChild(document.createTextNode(item));
    }});
    return div;
  }}

  const filterControl = L.control({{ position: 'topright' }});
  filterControl.onAdd = function() {{
    // Starts collapsed; only the media query above hides the body, so this
    // is a no-op above 600px and the panel stays always-expanded there.
    const div = L.DomUtil.create('div', 'filters collapsed');
    L.DomEvent.disableClickPropagation(div);
    L.DomEvent.disableScrollPropagation(div);

    const toggle = L.DomUtil.create('div', 'filters-toggle', div);
    L.DomUtil.create('span', '', toggle).textContent = 'Filters';
    L.DomUtil.create('span', 'chevron', toggle).textContent = '▾';
    toggle.onclick = () => div.classList.toggle('collapsed');

    const body = L.DomUtil.create('div', 'filters-body', div);
    const stats = L.DomUtil.create('div', 'stats', body);
    stats.id = 'stats-count';
    stats.textContent = `Showing ${{totalPlotted}} of ${{totalPlotted}} places`;
    if (failedCount > 0) {{
      const failedLine = L.DomUtil.create('div', 'stats failed', body);
      failedLine.textContent = `${{failedCount}} more failed to geocode (not shown)`;
    }}
    body.appendChild(document.createElement('hr'));
    body.appendChild(buildFilterGroup('Category', categories, activeCategories, c => colors[c] || '#333'));
    body.appendChild(document.createElement('hr'));
    body.appendChild(buildFilterGroup('Neighborhood', neighborhoods, activeNeighborhoods, null));
    if (cuisines.length) {{
      body.appendChild(document.createElement('hr'));
      body.appendChild(buildFilterGroup('Cuisine', cuisines, activeCuisines, null));
    }}
    return div;
  }};
  filterControl.addTo(map);

  refresh();
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("location", help="Location key, e.g. new_york (see data/<location>/)")
    parser.add_argument(
        "--output", default=None,
        help="Output HTML path (default: prototypes/leaflet_map/<location>.html)",
    )
    args = parser.parse_args()

    state = state_lib.load(paths.state_path(args.location))
    overrides_path = paths.overrides_path(args.location)

    core_bbox = None
    config_file = paths.config_path(args.location)
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        viewbox = config.get("viewbox")
        if viewbox:
            # "left,top,right,bottom" (Nominatim's viewbox format).
            left, top, right, bottom = (float(x) for x in viewbox.split(","))
            core_bbox = {"west": left, "south": bottom, "east": right, "north": top}

    cuisine_file = paths.cuisine_path(args.location)
    cuisine = {}
    if os.path.exists(cuisine_file):
        with open(cuisine_file, "r", encoding="utf-8") as f:
            cuisine = json.load(f)

    places = []
    for r in state.values():
        if r.get("status") != "success":
            continue
        title = r["title"]
        category, _ = categorize.categorize(
            title, r.get("tags", ""), r.get("osm_category"), r.get("osm_type"),
            overrides_path=overrides_path,
        )
        places.append({
            "title": title,
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "category": category,
            "neighborhood": r.get("neighborhood", ""),
            "cuisine": cuisine.get(title, ""),
            "url": r.get("url", ""),
        })

    total_tracked = len(state)
    failed_count = total_tracked - len(places)

    output_path = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), f"{args.location}.html"
    )
    html = HTML_TEMPLATE.format(
        location=args.location,
        places_json=json.dumps(places),
        colors_json=json.dumps(CATEGORY_COLORS),
        total_plotted=len(places),
        failed_count=failed_count,
        core_bbox_json=json.dumps(core_bbox),
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote {output_path} ({len(places)} places plotted, "
          f"{len(state) - len(places)} skipped - no successful geocode).")


if __name__ == "__main__":
    main()
