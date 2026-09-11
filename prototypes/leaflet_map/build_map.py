#!/usr/bin/env python3
"""Prototype: render a location's geocoded places as a self-contained Leaflet
map (OpenStreetMap tiles), colored by category.

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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))

from lib import paths
from lib import state as state_lib

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
  .legend {{
    background: white; padding: 8px 10px; border-radius: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3); font-size: 13px; line-height: 1.6;
  }}
  .legend .swatch {{
    display: inline-block; width: 10px; height: 10px; border-radius: 50%;
    margin-right: 6px;
  }}
</style>
</head>
<body>
<div id="map"></div>
<script>
  const places = {places_json};
  const colors = {colors_json};

  const map = L.map('map');
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }}).addTo(map);

  const bounds = [];
  const usedCategories = new Set();
  places.forEach(p => {{
    const color = colors[p.category] || '#333';
    usedCategories.add(p.category);
    const marker = L.circleMarker([p.lat, p.lon], {{
      radius: 7, color: color, fillColor: color, fillOpacity: 0.85, weight: 1,
    }}).addTo(map);
    marker.bindPopup(`<b>${{p.title}}</b><br>${{p.category}}<br>${{p.neighborhood || ''}}`);
    bounds.push([p.lat, p.lon]);
  }});
  if (bounds.length) {{ map.fitBounds(bounds, {{ padding: [30, 30] }}); }}
  else {{ map.setView([40.7128, -74.0060], 12); }}

  const legend = L.control({{ position: 'bottomright' }});
  legend.onAdd = function() {{
    const div = L.DomUtil.create('div', 'legend');
    let html = '<b>Category</b><br>';
    [...usedCategories].sort().forEach(cat => {{
      html += `<span class="swatch" style="background:${{colors[cat] || '#333'}}"></span>${{cat}}<br>`;
    }});
    div.innerHTML = html;
    return div;
  }};
  legend.addTo(map);
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
    places = [
        {
            "title": r["title"],
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "category": r.get("category", "Other/Uncategorized"),
            "neighborhood": r.get("neighborhood", ""),
        }
        for r in state.values()
        if r.get("status") == "success"
    ]

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
