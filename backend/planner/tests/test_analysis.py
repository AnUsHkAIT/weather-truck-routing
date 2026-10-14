from datetime import datetime, timezone

from django.test import SimpleTestCase

from planner.services.analysis import analyze_route
from planner.services.risk import SEVERE, NO_TRAVEL
from planner.services.weather import value_at

DEPART = datetime(2026, 10, 15, 8, 0, tzinfo=timezone.utc)


def steady_wind(mph):
    """Fake forecast: the same wind in every hour."""
    return {"time": ["2026-10-15T00:00"], "wind_speed_10m": [mph],
            "rain": [0], "snowfall": [0]}


def three_checkpoints():
    return [{"mile": m, "eta": DEPART, "lat": 0, "lon": 0} for m in (0, 10, 20)]


class ValueAtTests(SimpleTestCase):
    HOURLY = {
        "time": ["2026-10-15T00:00", "2026-10-15T01:00", "2026-10-15T02:00"],
        "wind_speed_10m": [10, 20, 30],
        "rain": [0, 0.1, 0.2],
        "snowfall": [0, 0, 0],
    }

    def test_picks_nearest_hour(self):
        eta = datetime(2026, 10, 15, 1, 20, tzinfo=timezone.utc)
        self.assertEqual(value_at(self.HOURLY, eta), (20, 0.1, 0))
        eta = datetime(2026, 10, 15, 1, 40, tzinfo=timezone.utc)
        self.assertEqual(value_at(self.HOURLY, eta), (30, 0.2, 0))

    def test_clamps_outside_the_data(self):
        early = datetime(2026, 10, 14, 0, 0, tzinfo=timezone.utc)
        late = datetime(2026, 10, 20, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(value_at(self.HOURLY, early)[0], 10)
        self.assertEqual(value_at(self.HOURLY, late)[0], 30)


class AnalyzeRouteTests(SimpleTestCase):
    def test_owned_miles_add_up_to_total(self):
        cps = three_checkpoints()
        analyze_route(cps, 20, 10_000, [steady_wind(0)] * 3)
        self.assertEqual([c["owned_miles"] for c in cps], [5, 10, 5])
        self.assertEqual(sum(c["owned_miles"] for c in cps), 20)

    def test_light_load_in_50_mph_wind_is_severe(self):
        stats = analyze_route(three_checkpoints(), 20, 20_000, [steady_wind(50)] * 3)
        self.assertEqual(stats["severe_miles"], 20)
        self.assertEqual(stats["max_risk"], SEVERE)

    def test_heavy_load_in_50_mph_wind_is_no_travel(self):
        stats = analyze_route(three_checkpoints(), 20, 35_000, [steady_wind(50)] * 3)
        self.assertEqual(stats["no_travel_miles"], 20)
        self.assertEqual(stats["max_risk"], NO_TRAVEL)

    def test_mixed_route_counts_miles_per_level(self):
        # Only the middle checkpoint has dangerous wind
        hourly = [steady_wind(0), steady_wind(50), steady_wind(0)]
        stats = analyze_route(three_checkpoints(), 20, 20_000, hourly)
        self.assertEqual(stats["severe_miles"], 10)
        self.assertEqual(stats["low_miles"], 10)
        self.assertAlmostEqual(stats["avg_risk"], 1.5)   # (3 * 10) / 20