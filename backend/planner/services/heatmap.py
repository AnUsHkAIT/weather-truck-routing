from datetime import timedelta

from .risk import assess
from .sampling import perpendicular_point, sample_route
from .weather import value_at

LATERAL_MI = 15        # how far each side of the route we sample
MAX_POINTS = 90       # keeps the weather request and the JSON small
HEATMAP_HOURS = 48


def corridor_points(routes, depart_utc):
    """(lat, lon) points along every route plus one on each side (the "corridor")."""
    longest = max(r["distance_mi"] for r in routes)
    step = max(25, round(longest / 20))            # about 20 samples on the longest route

    unique = {}
    for route in routes:
        samples, _ = sample_route(route["coords"], route["duration_s"], depart_utc, step=step)
        pts = [(s["lat"], s["lon"]) for s in samples]
        for i, here in enumerate(pts):
            before = pts[i - 1] if i > 0 else here
            after = pts[i + 1] if i < len(pts) - 1 else here
            for point in (here,
                          perpendicular_point(before, after, here, LATERAL_MI, 1),
                          perpendicular_point(before, after, here, LATERAL_MI, -1)):
                # round to ~0.7 mi so routes sharing a road don't repeat points
                unique[(round(point[0], 2), round(point[1], 2))] = point

    points = list(unique.values())
    if len(points) > MAX_POINTS:
        points = points[::-(-len(points) // MAX_POINTS)]      # ceil division = stride
    return points


def build_heatmap(points, hourly_list, load_lb, depart_utc, hours=HEATMAP_HOURS):
    """Risk level (0-4) at every point for every hour from departure: hours + 1 values."""
    out = []
    for (lat, lon), hourly in zip(points, hourly_list):
        levels = []
        for k in range(hours + 1):
            wind, rain, snow = value_at(hourly, depart_utc + timedelta(hours=k))
            levels.append(assess(wind, rain, snow, load_lb)[0])
        out.append({"lat": round(lat, 3), "lon": round(lon, 3), "levels": levels})
    return out