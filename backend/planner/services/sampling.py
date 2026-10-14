import math
from datetime import timedelta


def haversine_mi(a, b):
    """Straight-line distance in miles between two (lat, lon) points."""
    r = 3958.8  # Earth radius in miles
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(h))


def interval_for(total_miles):
    """The task says sample every 10 / 25 / 50 miles: pick by trip length."""
    if total_miles <= 200:
        return 10
    if total_miles <= 600:
        return 25
    return 50


def sample_route(coords, duration_s, depart_utc):
    """Return (checkpoints, total_miles).

    coords: [(lat, lon), ...] from the routing API
    duration_s: total drive time in seconds
    depart_utc: timezone-aware datetime in UTC

    Each checkpoint: {lat, lon, mile, eta}
    """
    # 1. Cumulative distance at every point of the line
    cum = [0.0]
    for p, q in zip(coords, coords[1:]):
        cum.append(cum[-1] + haversine_mi(p, q))
    total = cum[-1]
    if total == 0:
        return [{"lat": coords[0][0], "lon": coords[0][1],
                 "mile": 0.0, "eta": depart_utc}], 0.0

    # 2. The distances (in miles) where we want checkpoints
    step = interval_for(total)
    targets = [i * step for i in range(int(total // step) + 1)]
    if total - targets[-1] > 1:        # always include the destination
        targets.append(total)

    # 3. For each target, find the line segment it falls in and interpolate
    checkpoints, j = [], 0
    for t in targets:
        while j < len(cum) - 2 and cum[j + 1] < t:
            j += 1
        seg = (cum[j + 1] - cum[j]) or 1e-9
        f = min(max((t - cum[j]) / seg, 0.0), 1.0)
        lat = coords[j][0] + f * (coords[j + 1][0] - coords[j][0])
        lon = coords[j][1] + f * (coords[j + 1][1] - coords[j][1])
        # ETA assumes constant speed: time is proportional to distance
        eta = depart_utc + timedelta(seconds=duration_s * (t / total))
        checkpoints.append({"lat": lat, "lon": lon, "mile": round(t, 1), "eta": eta})

    return checkpoints, total