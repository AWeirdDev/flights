"""Unit tests for Google Flights result parsing."""

import json
import pathlib
import unittest

from fast_flights.parser import parse_js

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


class CapturedResponseTests(unittest.TestCase):
    """Parse a real response, trimmed to two itineraries with sparse times.

    Captured 2026-08-18 from a TPE-NRT economy search for 2026-09-01:

        js = LexborHTMLParser(fetch_flights_html(query)).css_first(r"script.ds\:1").text()
        payload = json.loads(js.split("data:", 1)[1].rsplit(",", 1)[0])

    Reduced to the two itineraries carrying sparse times. The best-flights
    section, the airline and alliance tables, and the per-search booking
    tokens are removed; the rest is as returned.
    """

    def setUp(self) -> None:
        payload = (FIXTURES / "tpe_nrt_sparse_times.json").read_text()
        self.flights = parse_js(f"data:{payload},ignored")

    def test_omitted_time_components_are_expanded(self) -> None:
        first, second = self.flights

        self.assertEqual(first.flights[0].departure.time, (1, 25))
        self.assertEqual(first.flights[0].arrival.time, (5, 0))  # [5]
        self.assertEqual(first.flights[1].departure.time, (7, 25))
        self.assertEqual(first.flights[1].arrival.time, (9, 55))
        self.assertEqual(second.flights[0].departure.time, (15, 30))
        self.assertEqual(second.flights[0].arrival.time, (20, 0))  # [20]

    def test_every_value_matches_its_declared_type(self) -> None:
        for flight in self.flights:
            for segment in flight.flights:
                for value in (segment.departure, segment.arrival):
                    self.assertIsInstance(value.time, tuple)
                    self.assertEqual(len(value.time), 2)
                    self.assertIsInstance(value.date, tuple)
                    self.assertEqual(len(value.date), 3)


def parse_time(value) -> tuple[int, int]:
    """Parse a payload carrying a single segment with the given departure."""
    segment = [None] * 22
    segment[3], segment[4] = "TPE", "Taiwan Taoyuan International Airport"
    segment[5], segment[6] = "Narita International Airport", "NRT"
    segment[8], segment[10] = value, [13, 5]
    segment[11], segment[17] = 205, "Airbus A350"
    segment[20] = segment[21] = [2026, 9, 1]

    flight = [None] * 23
    flight[0], flight[1], flight[2] = "nonstop", ["Test Airline"], [segment]
    flight[22] = [None] * 7 + [250000, 230000]

    payload = [None] * 8
    payload[3] = [[[flight, [[None, 12000]]]]]
    payload[7] = [None, [[], []]]
    return parse_js(f"data:{json.dumps(payload)},ignored")[0].flights[0].departure.time


class TimeEncodingTests(unittest.TestCase):
    """Shapes the captured fixture does not happen to contain."""

    def test_none_hour_becomes_zero(self) -> None:
        self.assertEqual(parse_time([None, 31]), (0, 31))  # 00:31

    def test_explicit_zero_is_preserved(self) -> None:
        self.assertEqual(parse_time([0, 0]), (0, 0))

    def test_absent_value_is_treated_as_midnight(self) -> None:
        self.assertEqual(parse_time([]), (0, 0))
        self.assertEqual(parse_time(None), (0, 0))
