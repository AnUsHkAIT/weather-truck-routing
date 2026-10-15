from datetime import timedelta

from .analysis import analyze_route
from .geocode import geocode
from .heatmap import HEATMAP_HOURS, build_heatmap, corridor_points
from .recommend import recommend
from .risk import LEVELS
from .routing import get_routes
from .sampling import sample_route
from .weather import fetch_hourly


def _simplify(coords, max_points=1500):
    """Thin out the route line so the JSON and the map stay light."""
    step = max(len(coords) // max_points, 1)
    thinned = coords[::step]
    if thinned[-1] != coords[-1]:
        thinned.append(coords[-1])
    return [[round(lat, 5), round(lon, 5)] for lat, lon in thinned]


def _public_checkpoint(cp):
    return {
        "mile": cp["mile"],
        "lat": round(cp["lat"], 5),
        "lon": round(cp["lon"], 5),
        "eta": cp["eta"].isoformat(),
        "wind_mph": round(cp["wind_mph"], 1),
        "rain_in_hr": round(cp["rain_in_hr"], 3),
        "snow_in_hr": round(cp["snow_in_hr"], 3),
        "risk": cp["risk"],
        "risk_label": cp["risk_label"],
        "reasons": cp["reasons"],
        "owned_miles": round(cp["owned_miles"], 1),
    }


def plan_trip(origin_text, destination_text, depart_utc, load_lb):
    origin = geocode(origin_text)
    destination = geocode(destination_text)
    routes = get_routes(origin, destination)

    # 1. Checkpoints (with ETAs) for each route, and the heatmap corridor
    sampled = [sample_route(r["coords"], r["duration_s"], depart_utc) for r in routes]
    route_points = [[(c["lat"], c["lon"]) for c in cps] for cps, _ in sampled]
    corridor = corridor_points(routes, depart_utc)

    # 2. One weather fetch (parallel chunks) for every point we need
    all_points = [p for pts in route_points for p in pts] + corridor
    longest_s = max(max(r["duration_s"] for r in routes), HEATMAP_HOURS * 3600)
    end_date = (depart_utc + timedelta(seconds=longest_s)).date().isoformat()
    hourly_all = fetch_hourly(all_points, depart_utc.date().isoformat(), end_date)

    # 3. Risk for each route
    results, cursor = [], 0
    for route, (checkpoints, miles), pts in zip(routes, sampled, route_points):
        hourly = hourly_all[cursor:cursor + len(pts)]
        cursor += len(pts)
        stats = analyze_route(checkpoints, miles, load_lb, hourly)
        results.append({
            "id": route["id"],
            "source": route["source"],
            "miles": round(miles, 1),
            "duration_s": round(route["duration_s"]),
            "arrival": (depart_utc + timedelta(seconds=route["duration_s"])).isoformat(),
            "geometry": _simplify(route["coords"]),
            "checkpoints": [_public_checkpoint(c) for c in checkpoints],
            **{k: round(v, 2) for k, v in stats.items()},
        })

    # 4. Recommendation and heatmap
    best = recommend(results)
    points = build_heatmap(corridor, hourly_all[cursor:], load_lb, depart_utc)

    return {
        "request": {
            "origin": origin, "destination": destination,
            "departure": depart_utc.isoformat(), "load_lb": load_lb,
        },
        "levels": LEVELS,
        "routes": results,
        "recommended_id": best["id"],
        "heatmap": {"start": depart_utc.isoformat(), "hours": HEATMAP_HOURS, "points": points},
    }