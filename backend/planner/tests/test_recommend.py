from django.test import SimpleTestCase

from planner.services.recommend import recommend


def route(id, nt=0, sev=0, high=0, avg=0.0, dur=3600):
    return {"id": id, "no_travel_miles": nt, "severe_miles": sev,
            "high_miles": high, "avg_risk": avg, "duration_s": dur}


def winner(*routes):
    return recommend(list(routes))["id"]


class RankingOrder(SimpleTestCase):
    def test_fewer_severe_miles_beats_everything_else(self):
        slow_but_safe = route(0, sev=0, high=300, avg=2.0, dur=9000)
        fast_but_severe = route(1, sev=10, high=0, avg=0.0, dur=3600)
        self.assertEqual(winner(slow_but_safe, fast_but_severe), 0)

    def test_no_travel_miles_come_before_severe(self):
        self.assertEqual(winner(route(0, nt=5), route(1, sev=100)), 1)

    def test_high_miles_break_a_severe_tie(self):
        self.assertEqual(winner(route(0, high=50), route(1, high=10)), 1)

    def test_average_risk_breaks_a_high_miles_tie(self):
        self.assertEqual(winner(route(0, avg=1.2), route(1, avg=0.4)), 1)

    def test_travel_time_is_the_last_tiebreaker(self):
        self.assertEqual(winner(route(0, dur=7200), route(1, dur=3600)), 1)

    def test_sub_mile_differences_are_ignored(self):
        # 0.4 High miles rounds to 0, so the faster route wins
        self.assertEqual(winner(route(0, high=0.0, dur=7200),
                                route(1, high=0.4, dur=3600)), 1)


class Labels(SimpleTestCase):
    def test_only_the_winner_is_marked_recommended(self):
        routes = [route(0, high=50), route(1, high=0)]
        recommend(routes)
        self.assertEqual([r["recommended"] for r in routes], [False, True])

    def test_explanation_names_the_winner_and_the_numbers(self):
        routes = [route(0, high=50, dur=3600), route(1, high=0, dur=7200)]
        best = recommend(routes)
        self.assertIn("Route B is recommended", best["explanation"])
        self.assertIn("50", best["explanation"])
        self.assertIn("longer", best["explanation"])

    def test_no_travel_route_is_flagged(self):
        routes = [route(0, nt=20), route(1)]
        recommend(routes)
        self.assertTrue(routes[0]["status"].startswith("Not advised"))
        self.assertEqual(routes[1]["status"], "OK")

    def test_warning_when_every_route_has_no_travel(self):
        best = recommend([route(0, nt=20), route(1, nt=30)])
        self.assertIn("Warning", best["explanation"])