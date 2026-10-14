from django.test import SimpleTestCase

from planner.services.risk import (
    assess, LOW, MODERATE, HIGH, SEVERE, NO_TRAVEL,
)


class WindThresholds(SimpleTestCase):
    def test_wind_boundaries(self):
        cases = [
            (0, LOW), (24.9, LOW),
            (25, MODERATE), (34.9, MODERATE),
            (35, HIGH), (44.9, HIGH),
            (45, SEVERE), (54.9, SEVERE),
            (55, NO_TRAVEL), (80, NO_TRAVEL),
        ]
        for wind, expected in cases:
            with self.subTest(wind=wind):
                self.assertEqual(assess(wind, 0, 0, 0)[0], expected)


class RainThresholds(SimpleTestCase):
    def test_rain_boundaries(self):
        cases = [
            (0, LOW), (0.09, LOW),
            (0.10, MODERATE), (0.24, MODERATE),
            (0.25, HIGH), (0.49, HIGH),
            (0.50, SEVERE), (1.00, SEVERE),     # 1.00 is still Severe
            (1.01, NO_TRAVEL),
        ]
        for rain, expected in cases:
            with self.subTest(rain=rain):
                self.assertEqual(assess(0, rain, 0, 0)[0], expected)


class SnowThresholds(SimpleTestCase):
    def test_snow_boundaries(self):
        cases = [
            (0.49, LOW),
            (0.5, MODERATE), (0.99, MODERATE),
            (1.0, HIGH), (1.99, HIGH),
            (2.0, SEVERE), (3.0, SEVERE),       # 3.0 is still Severe
            (3.01, NO_TRAVEL),
        ]
        for snow, expected in cases:
            with self.subTest(snow=snow):
                self.assertEqual(assess(0, 0, snow, 0)[0], expected)


class LoadRules(SimpleTestCase):
    def test_wind_55_is_no_travel_for_any_load(self):
        self.assertEqual(assess(55, 0, 0, 0)[0], NO_TRAVEL)
        self.assertEqual(assess(60, 0, 0, 1000)[0], NO_TRAVEL)

    def test_wind_45_to_54_heavy_load_is_no_travel(self):
        self.assertEqual(assess(50, 0, 0, 31_000)[0], NO_TRAVEL)

    def test_wind_45_to_54_light_load_stays_severe(self):
        self.assertEqual(assess(50, 0, 0, 30_000)[0], SEVERE)  # not ">" 30,000

    def test_wind_35_to_44_very_heavy_load_is_severe(self):
        self.assertEqual(assess(40, 0, 0, 45_000)[0], SEVERE)

    def test_wind_35_to_44_exactly_40000_stays_high(self):
        self.assertEqual(assess(40, 0, 0, 40_000)[0], HIGH)    # not ">" 40,000

    def test_load_rule_never_lowers_risk(self):
        # Heavy rain already makes this Severe; a load rule must not reduce it.
        self.assertEqual(assess(36, 0.8, 0, 45_000)[0], SEVERE)


class Combinations(SimpleTestCase):
    def test_worst_factor_wins(self):
        level, _ = assess(wind_mph=10, rain_in_hr=0.3, snow_in_hr=0, load_lb=0)
        self.assertEqual(level, HIGH)

    def test_missing_values_default_to_low(self):
        self.assertEqual(assess(None, None, None, 20_000)[0], LOW)

    def test_reasons_are_explained(self):
        _, reasons = assess(50, 0, 0, 31_000)
        self.assertTrue(any("no travel" in r.lower() for r in reasons))