"""
Weather risk rules for one checkpoint.

Boundary convention: lower bounds are inclusive. The table overlaps at
values like 0.25 in/hr (end of Moderate, start of High), so 0.25 is High.
"No Travel" is written as ">1.00" and ">3.0" for rain and snow, so exactly
1.00 in/hr rain is still Severe. Wind "No Travel" is ">= 55", so 55 is No Travel.
"""

LEVELS = ["Low", "Moderate", "High", "Severe", "No Travel"]
LOW, MODERATE, HIGH, SEVERE, NO_TRAVEL = range(5)

# Upper bounds of Low / Moderate / High / Severe
WIND = (25, 35, 45, 55)           # mph
RAIN = (0.10, 0.25, 0.50, 1.00)   # in/hr
SNOW = (0.5, 1.0, 2.0, 3.0)       # in/hr


def band(value, cuts, top_inclusive=False):
    """Map a measurement to a risk level 0-4 using the 4 cut points."""
    for level in range(3):
        if value < cuts[level]:
            return level
    top = cuts[3]
    is_severe = value <= top if top_inclusive else value < top
    return SEVERE if is_severe else NO_TRAVEL


def assess(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    """Return (risk_level, reasons) for one checkpoint.

    Missing weather values (None) are treated as 0, meaning Low.
    """

    if wind_mph is None or rain_in_hr is None or snow_in_hr is None:
        raise ValueError(
            "Cannot calculate weather risk when a weather measurement is missing."
        )

    if load_lb is None:
        raise ValueError("Load weight is required to calculate weather risk.")

    wind = wind_mph
    rain = rain_in_hr
    snow = snow_in_hr
    load = load_lb
    wind_lvl = band(wind, WIND)
    rain_lvl = band(rain, RAIN, top_inclusive=True)
    snow_lvl = band(snow, SNOW, top_inclusive=True)
    level = max(wind_lvl, rain_lvl, snow_lvl)

    reasons = []
    for name, value, unit, lvl in (
        ("Wind", wind, "mph", wind_lvl),
        ("Rain", rain, "in/hr", rain_lvl),
        ("Snow", snow, "in/hr", snow_lvl),
    ):
        if lvl > LOW:
            reasons.append(f"{name} {value:.2f} {unit}: {LEVELS[lvl]}")

    # Load rules (these can only raise the level, never lower it)
    if wind >= 55:
        level = NO_TRAVEL
        reasons.append("Wind >= 55 mph: no travel for any load")
    elif 45 <= wind < 55 and load > 30_000:
        level = NO_TRAVEL
        reasons.append("Wind 45-54 mph with load > 30,000 lb: no travel")
    elif 35 <= wind < 45 and load > 40_000:
        level = max(level, SEVERE)
        reasons.append("Wind 35-44 mph with load > 40,000 lb: severe")

    return level, reasons