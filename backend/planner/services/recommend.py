"""Pick the best route.

Priority order (from the task), compared lexicographically:
  1. Fewest Severe miles
  2. Fewest High miles
  3. Lowest average risk
  4. Shortest travel time

Design decision: "No Travel" miles are compared BEFORE Severe miles,
because a No Travel stretch is worse than a Severe one.
"""

NO_TRAVEL_WARNING = (
    " Warning: even the best route has No Travel conditions, "
    "so consider a different departure time."
)

# (label, formatter) in priority order; must match rank_key below
CRITERIA = [
    ("No Travel miles", lambda r: f"{r['no_travel_miles']:.0f}"),
    ("Severe miles", lambda r: f"{r['severe_miles']:.0f}"),
    ("High miles", lambda r: f"{r['high_miles']:.0f}"),
    ("average risk", lambda r: f"{r['avg_risk']:.2f}"),
    ("travel time", lambda r: f"{r['duration_s'] / 3600:.1f} h"),
]


def rank_key(route):
    """Lower is better. Miles are rounded to whole miles so that a 0.4 mile
    difference (just checkpoint spacing noise) can't decide the winner."""
    return (
        round(route["no_travel_miles"]),
        round(route["severe_miles"]),
        round(route["high_miles"]),
        round(route["avg_risk"], 2),
        route["duration_s"],
    )


def _compare(best, other):
    """One sentence: the first criterion where `best` beats `other`."""
    best_key, other_key = rank_key(best), rank_key(other)
    last = len(CRITERIA) - 1
    for i, (label, fmt) in enumerate(CRITERIA):
        if best_key[i] != other_key[i]:
            sentence = f"{label} {fmt(best)} vs {fmt(other)} on {other['name']}"
            extra_hours = (best["duration_s"] - other["duration_s"]) / 3600
            if i < last and extra_hours > 0.05:
                sentence += f" (takes {extra_hours:.1f} h longer)"
            return sentence
    return f"same as {other['name']} on every measure"


def recommend(routes):
    """Mark the best route in place and return it.

    Adds to every route: name, recommended, status.
    Adds to the winner: explanation.
    """
    for route in routes:
        route["name"] = f"Route {chr(65 + route['id'])}"      # A, B, C

    best = min(routes, key=rank_key)
    others = [r for r in routes if r is not best]

    for route in routes:
        route["recommended"] = route is best
        route["status"] = (
            "Not advised: No Travel conditions" if route["no_travel_miles"] > 0 else "OK"
        )

    if others:
        details = "; ".join(_compare(best, o) for o in others)
        text = f"{best['name']} is recommended: {details}."
    else:
        text = f"{best['name']} is the only route available."
    if best["no_travel_miles"] > 0:
        text += NO_TRAVEL_WARNING
    best["explanation"] = text
    return best