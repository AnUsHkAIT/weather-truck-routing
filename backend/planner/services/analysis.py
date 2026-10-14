from .risk import LEVELS, LOW, MODERATE, HIGH, SEVERE, NO_TRAVEL, assess
from .weather import value_at


def analyze_route(checkpoints, total_miles, load_lb, hourly_list):
    """Attach weather and risk to every checkpoint and return route-level stats.

    Each checkpoint "owns" the stretch of road halfway to its neighbours.
    Adding up the owned miles per risk level gives Severe miles, High miles, etc.
    """
    # 1. Weather and risk at each checkpoint's ETA
    for cp, hourly in zip(checkpoints, hourly_list):
        wind, rain, snow = value_at(hourly, cp["eta"])
        level, reasons = assess(wind, rain, snow, load_lb)
        cp.update(
            wind_mph=wind or 0,
            rain_in_hr=rain or 0,
            snow_in_hr=snow or 0,
            risk=level,
            risk_label=LEVELS[level],
            reasons=reasons,
        )

    # 2. Miles owned by each checkpoint (halfway to the previous and next one)
    n = len(checkpoints)
    for i, cp in enumerate(checkpoints):
        start = (checkpoints[i - 1]["mile"] + cp["mile"]) / 2 if i > 0 else 0
        end = (cp["mile"] + checkpoints[i + 1]["mile"]) / 2 if i < n - 1 else total_miles
        cp["owned_miles"] = max(end - start, 0)

    # 3. Route-level totals
    def miles_at(level):
        return sum(c["owned_miles"] for c in checkpoints if c["risk"] == level)

    weighted = sum(c["risk"] * c["owned_miles"] for c in checkpoints)
    return {
        "no_travel_miles": miles_at(NO_TRAVEL),
        "severe_miles": miles_at(SEVERE),
        "high_miles": miles_at(HIGH),
        "moderate_miles": miles_at(MODERATE),
        "low_miles": miles_at(LOW),
        "avg_risk": weighted / total_miles if total_miles else 0,   # 0 (Low) to 4 (No Travel)
        "max_risk": max((c["risk"] for c in checkpoints), default=0),
    }