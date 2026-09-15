"""Client for the Google Geocoding API - used as a fallback for places
Nominatim (OpenStreetMap) can't find, since OSM coverage for small/newer
businesses is spotty (see decisions/0002 and 0005).

Requires GOOGLE_MAPS_API_KEY in the environment. Costs money per call (see
https://mapsplatform.google.com/pricing/) - only call this after Nominatim
has already failed.
"""

import os
import requests

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

# https://developers.google.com/maps/documentation/geocoding/requests-geocoding#Types
HIGH_CONFIDENCE_TYPES = {
    "establishment", "point_of_interest", "premise", "subpremise",
}


class GeocodeError(Exception):
    pass


def _api_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        raise GeocodeError("GOOGLE_MAPS_API_KEY not set in environment")
    return key


def search(query: str, bounds: str | None = None) -> list[dict]:
    """Search the Google Geocoding API for `query`.

    `bounds` is "south,west|north,east" and only biases results (unlike
    Nominatim's `bounded=1`, Google has no hard viewport restriction on the
    free geocode endpoint).

    Raises GeocodeError on request failure or a non-OK/ZERO_RESULTS status.
    Returns [] for ZERO_RESULTS (mirrors nominatim.search's empty-list-on-
    no-match behavior).
    """
    params = {"address": query, "key": _api_key()}
    if bounds:
        params["bounds"] = bounds

    try:
        resp = requests.get(GEOCODE_URL, params=params, timeout=20)
    except requests.RequestException as exc:
        raise GeocodeError(f"request failed: {exc}") from exc

    if resp.status_code != 200:
        raise GeocodeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    status = data.get("status")
    if status == "ZERO_RESULTS":
        return []
    if status != "OK":
        raise GeocodeError(f"{status}: {data.get('error_message', '')}")

    return data.get("results", [])


def _match_confidence(result: dict) -> str:
    types = set(result.get("types", []))
    return "high" if types & HIGH_CONFIDENCE_TYPES else "low"


def to_nominatim_shape(result: dict) -> dict:
    """Adapt a Google Geocoding result into the subset of Nominatim's
    result shape that src/geocode.py reads, so callers don't need to know
    which provider answered.
    """
    location = result["geometry"]["location"]
    address_components = result.get("address_components", [])

    def component(*types: str) -> str | None:
        for c in address_components:
            if set(c["types"]) & set(types):
                return c["long_name"]
        return None

    neighborhood = component("neighborhood", "sublocality", "locality")
    city = component("locality", "postal_town")

    return {
        "lat": str(location["lat"]),
        "lon": str(location["lng"]),
        "display_name": result.get("formatted_address", ""),
        "address": {
            "house_number": component("street_number"),
            "road": component("route"),
            "city": city,
            "state": component("administrative_area_level_1"),
            "postcode": component("postal_code"),
            "neighbourhood": neighborhood,
        },
        "addresstype": None,
        "category": None,
        "type": None,
        "_google_match_confidence": _match_confidence(result),
        "_source": "google",
    }
