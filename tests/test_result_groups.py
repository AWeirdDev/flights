# [AI CONTENT]
"""Synthetic regression coverage; no live requests or booking tokens."""

import json
import unittest

from fast_flights.parser import parse_js


def itinerary(price):
    segment = [None] * 22
    segment[3:7] = ["AAA", "Origin", "Destination", "BBB"]
    segment[8], segment[10] = [9], [11]
    segment[11], segment[17] = 120, "Test aircraft"
    segment[20] = segment[21] = [2026, 10, 1]
    flight = [None] * 23
    flight[0:3] = ["nonstop", ["Test Airline"], [segment]]
    flight[22] = [None] * 7 + [100000, 120000]
    return [flight, [price]]


def parse_groups(best, other):
    payload = [None] * 8
    payload[2], payload[3] = best, other
    payload[7] = [None, [[["TEST", "Test Alliance"]], [["TA", "Test Airline"]]]]
    return parse_js(f"data:{json.dumps(payload)},ignored")


class ResultGroupTests(unittest.TestCase):
    def test_both_groups_are_returned_in_order(self):
        flights = parse_groups([[itinerary([None, 100])]], [[itinerary([None, 200])]])
        self.assertEqual([f.price for f in flights], [100, 200])

    def test_each_group_can_be_absent_or_empty(self):
        for empty in (None, [], [None], [[]]):
            for best, other in ((empty, [[itinerary([None, 100])]]),
                                ([[itinerary([None, 100])]], empty)):
                with self.subTest(best=best, other=other):
                    self.assertEqual([f.price for f in parse_groups(best, other)], [100])

    def test_missing_price_preserves_itinerary_and_following_results(self):
        for fare in ([], [None], [None, None]):
            with self.subTest(fare=fare):
                flights = parse_groups(None, [[itinerary(fare), itinerary([None, 200])]])
                self.assertEqual([f.price for f in flights], [None, 200])
                self.assertEqual(flights[0].flights[0].from_airport.code, "AAA")

    def test_zero_price_is_not_missing(self):
        self.assertEqual(parse_groups(None, [[itinerary([None, 0])]])[0].price, 0)

    def test_empty_results_retain_metadata(self):
        flights = parse_groups([None], [None])
        self.assertEqual(flights, [])
        self.assertEqual(flights.metadata.airlines[0].code, "TA")
# [/AI CONTENT]
