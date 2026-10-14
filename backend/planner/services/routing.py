import polyline
import requests
from django.conf import settings

from .errors import RoutingError, TripPlannerError, UpstreamError
from .sampling import haversine_mi, perpendicular_point

DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{coords}"
METERS_PER_MILE = 1609.344
MAX_ROUTES = 3
TRUCK_MAX_AVG_MPH = 55      # Mapbox uses car speeds; loaded trucks are slower
DUPLICATE_GAP_MI = 2.0      # routes closer than this on average are "the same"
MAX_DETOUR_RATIO = 1.6      # reject detours more than 60% longer than the best route


def _fetch(waypoints, alternatives):
    """Call Mapbox through [{'lat','lon'}, ...] and return the routes it finds."""
    coords = ";".join(f"{p['lon']},{p['lat']}" for p in waypoints)
    params = {
        "alternatives": "true" if alternatives else "false",
        "geometries": "polyline6",
        "overview": "full",
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
            "coords": polyline.decode(rt["geometry"], 6),   # [(lat, lon), ...]
            "distance_mi": rt["distance"] / METERS_PER_MILE,
            "duration_s": rt["duration"],
            "source": "mapbox",
        }
        for rt in raw
    ]


# ---------- near-duplicate detection ----------

def _gap(a, b):
    """Average distance (miles) from points on line `a` to the nearest point on `b`."""
    sample_a = a[::max(len(a) // 30, 1)]
    sample_b = b[::max(len(b) // 2000, 1)]
    total = sum(min(haversine_mi(p, q) for q in sample_b) for p in sample_a)
    return total / len(sample_a)


def is_duplicate(a, b):
    """True if two route lines follow essentially the same roads."""
    return _gap(a, b) < DUPLICATE_GAP_MI and _gap(b, a) < DUPLICATE_GAP_MI


def _dedupe(routes):
    kept = []
    for route in routes:
        if not any(is_duplicate(route["coords"], k["coords"]) for k in kept):
            kept.append(route)
    return kept


# ---------- forcing a 3rd route ----------

def via_point(origin, destination, offset_mi, side=1):
    """A point beside the midpoint of the trip, `offset_mi` off the straight line."""
    a = (origin["lat"], origin["lon"])
    b = (destination["lat"], destination["lon"])
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    lat, lon = perpendicular_point(a, b, mid, offset_mi, side)
    return {"lat": lat, "lon": lon}


def _add_detours(origin, destination, routes):
    """Ask Mapbox to route through a side point until we have MAX_ROUTES."""
    base = routes[0]
    offset = min(max(base["distance_mi"] * 0.08, 10), 50)
    for scale in (1, 2):                       # try a small, then a bigger detour
        for side in (1, -1):                   # left side, then right side
            if len(routes) >= MAX_ROUTES:
                return routes
            via = via_point(origin, destination, offset * scale, side)
            try:
                candidate = _fetch([origin, via, destination], alternatives=False)[0]
            except TripPlannerError:
                continue                       # this detour failed, try the next
            if candidate["distance_mi"] > base["distance_mi"] * MAX_DETOUR_RATIO:
                continue                       # absurdly long
            if any(is_duplicate(candidate["coords"], r["coords"]) for r in routes):
                continue
            candidate["source"] = "detour"
            routes.append(candidate)
    return routes


# ---------- public function ----------

def _apply_truck_speed(route):
    """Never assume a faster average speed than TRUCK_MAX_AVG_MPH."""
    slowest = route["distance_mi"] / TRUCK_MAX_AVG_MPH * 3600
    route["duration_s"] = max(route["duration_s"], slowest)


def get_routes(origin, destination):
    """Return up to 3 distinct routes: {id, coords, distance_mi, duration_s, source}."""
    routes = _dedupe(_fetch([origin, destination], alternatives=True))
    if len(routes) < MAX_ROUTES:
        routes = _add_detours(origin, destination, routes)
    routes = routes[:MAX_ROUTES]
    for i, route in enumerate(routes):
        route["id"] = i
        _apply_truck_speed(route)
    return routes