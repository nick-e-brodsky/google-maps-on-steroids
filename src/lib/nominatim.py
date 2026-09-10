"""Rate-limited, retrying client for the public Nominatim search API.

Usage policy (https://operations.osmfoundation.org/policies/nominatim/) requires:
- a descriptive User-Agent identifying the tool/contact
- max 1 request/second to the public endpoint
"""

import time
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = (
    "google-maps-on-steroids/0.1 "
    "(personal travel-list geocoding tool; contact: nick.e.brodsky@gmail.com)"
)
MIN_REQUEST_INTERVAL = 1.1  # seconds, stays above the 1 req/sec policy limit
MAX_ATTEMPTS = 5
BACKOFF_BASE = 2  # seconds; doubles each attempt: 2, 4, 8, 16, 32

_last_request_time = 0.0


class GeocodeError(Exception):
    pass


def _throttle():
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    wait = MIN_REQUEST_INTERVAL - elapsed
    if wait > 0:
        time.sleep(wait)
    _last_request_time = time.monotonic()


def search(query: str, viewbox: str | None = None) -> list[dict]:
    """Search Nominatim for `query`. Retries transient failures with backoff.

    `viewbox` (left,top,right,bottom) restricts matches to a bounding box -
    keeps free-text matches from drifting to same-named places elsewhere
    (e.g. a business called "EDEN" matching a town instead of the actual
    venue). Pass the target location's bounding box; omit for an unbounded
    worldwide search.

    Raises GeocodeError if all attempts are exhausted.
    """
    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1,
    }
    if viewbox:
        params["viewbox"] = viewbox
        params["bounded"] = 1

    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        _throttle()
        try:
            resp = requests.get(
                NOMINATIM_URL,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=20,
            )
        except requests.RequestException as exc:
            last_error = exc
        else:
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError as exc:
                    last_error = exc
            elif resp.status_code == 429:
                last_error = GeocodeError("rate limited (429)")
            elif 500 <= resp.status_code < 600:
                last_error = GeocodeError(f"server error ({resp.status_code})")
            else:
                # Non-retriable client error (e.g. 400) - fail fast.
                raise GeocodeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_BASE * (2 ** (attempt - 1)))

    raise GeocodeError(f"exhausted {MAX_ATTEMPTS} attempts: {last_error}")
