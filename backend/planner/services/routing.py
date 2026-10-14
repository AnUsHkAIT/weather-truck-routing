import polyline
import requests
from django.conf import settings

from .errors import RoutingError, UpstreamError

DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{coords}"
METERS_PER_MILE = 1609.344


def get_routes(origin, destination):
    """Return up to 3 routes between two {'lat','lon'} points.

    Each route: {id, coords: [(lat, lon), ...], distance_mi, duration_s}
    """
    coords = f"{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}"
    params = {
        "alternatives": "true",       # ask for alternative routes
        "geometries": "polyline6",    # compact + precise encoding
        "overview": "full",           # full-detail line, not simplified
        "access_token": settings.MAPBOX_TOKEN,
    }
    try:
        resp = requests.get(DIRECTIONS_URL.format(coords=coords), params=params, timeout=25)
    except requests.RequestException as exc:
        raise UpstreamError("Routing service is unreachable.") from exc

    if resp.status_code != 200:
        raise UpstreamError(f"Routing service error ({resp.status_code}).")

    raw = resp.json().get("routes", [])
    if not raw:
        raise RoutingError("No drivable route found between those locations.")

    return [
        {
            "id": i,
            "coords": polyline.decode(rt["geometry"], 6),   # -> [(lat, lon), ...]
            "distance_mi": rt["distance"] / METERS_PER_MILE,
            "duration_s": rt["duration"],
        }
        for i, rt in enumerate(raw[:3])
    ]