import math
from datetime import timedelta


def haversine_mi(a, b):
    """Straight-line distance in miles between two (lat, lon) points."""
    r = 3958.8
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))

    h = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1)
        * math.cos(la2)
        * math.sin((lo2 - lo1) / 2) ** 2
    )

    return 2 * r * math.asin(math.sqrt(h))


def interval_for(total_miles):
    """Choose a checkpoint interval based on trip length."""
    if total_miles <= 200:
        return 10
    if total_miles <= 600:
        return 25
    return 50


def perpendicular_point(a, b, base, miles, side=1):
    """Return a point offset to the left or right of the line a -> b.

    a, b, base are (lat, lon).
    side=1 is left of travel; side=-1 is right.
    """
    cos_lat = math.cos(math.radians(base[0])) or 1e-9

    dx = (b[1] - a[1]) * cos_lat
    dy = b[0] - a[0]

    length = math.hypot(dx, dy) or 1e-9

    px, py = -dy / length, dx / length
    degrees = miles / 69.0

    return (
        base[0] + side * py * degrees,
        base[1] + side * px * degrees / cos_lat,
    )


def sample_route(coords, duration_s, depart_utc, step=None):
    """Return (checkpoints, total_miles).

    coords: [(lat, lon), ...] from the routing API
    duration_s: total drive time in seconds
    depart_utc: timezone-aware datetime in UTC
    step: optional custom checkpoint interval in miles

    Each checkpoint contains lat, lon, mile, and eta.
    """
    if not coords:
        return [], 0.0

    # 1. Calculate cumulative distance along the route.
    cum = [0.0]

    for p, q in zip(coords, coords[1:]):
        cum.append(cum[-1] + haversine_mi(p, q))

    total = cum[-1]

    if total == 0:
        return [
            {
                "lat": coords[0][0],
                "lon": coords[0][1],
                "mile": 0.0,
                "eta": depart_utc,
            }
        ], 0.0

    # 2. Choose checkpoint intervals.
    step = step or interval_for(total)

    targets = [i * step for i in range(int(total // step) + 1)]

    # Always include the destination.
    if total - targets[-1] > 1:
        targets.append(total)

    # 3. Interpolate each checkpoint along the route.
    checkpoints = []
    j = 0

    for t in targets:
        while j < len(cum) - 2 and cum[j + 1] < t:
            j += 1

        seg = (cum[j + 1] - cum[j]) or 1e-9

        f = min(max((t - cum[j]) / seg, 0.0), 1.0)

        lat = coords[j][0] + f * (coords[j + 1][0] - coords[j][0])
        lon = coords[j][1] + f * (coords[j + 1][1] - coords[j][1])

        # Estimate arrival time proportional to distance traveled.
        eta = depart_utc + timedelta(
            seconds=duration_s * (t / total)
        )

        checkpoints.append({
            "lat": lat,
            "lon": lon,
            "mile": round(t, 1),
            "eta": eta,
        })

    return checkpoints, total