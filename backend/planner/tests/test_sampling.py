from datetime import datetime, timezone

from django.test import SimpleTestCase

from planner.services.sampling import haversine_mi, interval_for, sample_route

DEPART = datetime(2026, 10, 15, 8, 0, tzinfo=timezone.utc)


class HaversineTests(SimpleTestCase):
    def test_same_point_is_zero(self):
        self.assertEqual(haversine_mi((10, 20), (10, 20)), 0)

    def test_one_degree_of_longitude_at_equator(self):
        self.assertAlmostEqual(haversine_mi((0, 0), (0, 1)), 69.09, delta=0.2)


class IntervalTests(SimpleTestCase):
    def test_interval_by_trip_length(self):
        cases = [(50, 10), (200, 10), (201, 25), (600, 25), (601, 50)]
        for miles, expected in cases:
            with self.subTest(miles=miles):
                self.assertEqual(interval_for(miles), expected)


class SampleRouteTests(SimpleTestCase):
    def setUp(self):
        # A straight line of about 69 miles along the equator, driven in 1 hour
        self.points, self.total = sample_route([(0, 0), (0, 1)], 3600, DEPART)

    def test_total_miles(self):
        self.assertAlmostEqual(self.total, 69.09, delta=0.2)

    def test_first_checkpoint_is_origin_at_departure_time(self):
        self.assertEqual(self.points[0]["mile"], 0)
        self.assertEqual(self.points[0]["eta"], DEPART)

    def test_last_checkpoint_is_destination_at_arrival_time(self):
        last = self.points[-1]
        self.assertAlmostEqual(last["mile"], self.total, delta=0.1)
        seconds = (last["eta"] - DEPART).total_seconds()
        self.assertAlmostEqual(seconds, 3600, delta=1)

    def test_checkpoints_are_10_miles_apart(self):
        miles = [p["mile"] for p in self.points]
        self.assertEqual(miles[:4], [0, 10, 20, 30])

    def test_etas_only_move_forward(self):
        etas = [p["eta"] for p in self.points]
        self.assertEqual(etas, sorted(etas))