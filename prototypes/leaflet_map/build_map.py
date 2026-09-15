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
<title>{location} - Leaflet prototype</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body {{ margin: 0; height: 100%; font-family: system-ui, sans-serif; }}
  #map {{ height: 100%; }}
  .filters {{
    background: white; padding: 10px 12px; border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3); font-size: 13px; line-height: 1.5;
    max-height: 70vh; overflow-y: auto; width: 220px;
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
  .count {{ color: #888; font-size: 11px; }}
</style>
</head>
<body>
<div id="map"></div>
<script>
  const places = {places_json};
  const colors = {colors_json};

  const categories = [...new Set(places.map(p => p.category))].sort();
  const neighborhoods = [...new Set(places.map(p => p.neighborhood).filter(Boolean))].sort();

  const map = L.map('map');
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }}).addTo(map);

  const activeCategories = new Set(categories);
  const activeNeighborhoods = new Set(neighborhoods);

  const markers = places.map(p => {{
    const color = colors[p.category] || '#333';
    const marker = L.circleMarker([p.lat, p.lon], {{
      radius: 7, color: color, fillColor: color, fillOpacity: 0.85, weight: 1,
    }});
    const cuisineLine = p.cuisine ? `<br>${{p.cuisine}} cuisine` : '';
    marker.bindPopup(`<b>${{p.title}}</b><br>${{p.category}}${{cuisineLine}}<br>${{p.neighborhood || ''}}`);
    return {{ marker, place: p }};
  }});

  function applyFilters() {{
    const bounds = [];
    markers.forEach(({{ marker, place }}) => {{
      const visible = activeCategories.has(place.category) &&
        (place.neighborhood === '' || activeNeighborhoods.has(place.neighborhood));
      if (visible) {{
        if (!map.hasLayer(marker)) marker.addTo(map);
        bounds.push([place.lat, place.lon]);
      }} else if (map.hasLayer(marker)) {{
        map.removeLayer(marker);
      }}
    }});
    return bounds;
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
      applyFilters();
    }};
    items.forEach(item => {{
      const label = L.DomUtil.create('label', '', div);
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = true;
      cb.onchange = () => {{
        if (cb.checked) activeSet.add(item); else activeSet.delete(item);
        applyFilters();
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
    const div = L.DomUtil.create('div', 'filters');
    L.DomEvent.disableClickPropagation(div);
    L.DomEvent.disableScrollPropagation(div);
    div.appendChild(buildFilterGroup('Category', categories, activeCategories, c => colors[c] || '#333'));
    div.appendChild(document.createElement('hr'));
    div.appendChild(buildFilterGroup('Neighborhood', neighborhoods, activeNeighborhoods, null));
    return div;
  }};
  filterControl.addTo(map);

  const bounds = applyFilters();
  if (bounds.length) {{ map.fitBounds(bounds, {{ padding: [30, 30] }}); }}
  else {{ map.setView([40.7128, -74.0060], 12); }}
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
        })

    output_path = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), f"{args.location}.html"
    )
    html = HTML_TEMPLATE.format(
        location=args.location,
        places_json=json.dumps(places),
        colors_json=json.dumps(CATEGORY_COLORS),
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote {output_path} ({len(places)} places plotted, "
          f"{len(state) - len(places)} skipped - no successful geocode).")


if __name__ == "__main__":
    main()
