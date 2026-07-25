"""Unit tests for Google Flights query serialization."""

import unittest

from fast_flights import FlightQuery, create_query
from fast_flights.pb.flights_pb2 import Emissions, Info


class QueryingTests(unittest.TestCase):
    def test_default_query_does_not_add_optional_filters(self) -> None:
        query = create_query(
            flights=[
                FlightQuery(
                    date="2099-01-02",
                    from_airport="MSP",
                    to_airport="SLC",
                )
            ]
        )

        info = Info.FromString(query.to_bytes())
        flight = info.data[0]

        self.assertFalse(info.HasField("max_price"))
        self.assertFalse(info.HasField("baggage"))
        self.assertFalse(info.HasField("hide_separate_and_self_transfer"))
        self.assertFalse(info.HasField("exclude_basic_economy"))
        self.assertFalse(flight.HasField("earliest_departure_hour"))
        self.assertFalse(flight.HasField("latest_departure_hour"))
        self.assertFalse(flight.HasField("earliest_arrival_hour"))
        self.assertFalse(flight.HasField("latest_arrival_hour"))
        self.assertFalse(flight.HasField("max_duration_minutes"))
        self.assertFalse(flight.HasField("min_layover_minutes"))
        self.assertFalse(flight.HasField("max_layover_minutes"))
        self.assertEqual(list(flight.connecting_airports), [])
        self.assertEqual(list(flight.emissions), [])

    def test_serializes_per_leg_filters(self) -> None:
        query = create_query(
            flights=[
                FlightQuery(
                    date="2099-01-02",
                    from_airport="MSP",
                    to_airport="SLC",
                    earliest_departure_hour=7,
                    latest_departure_hour=18,
                    earliest_arrival_hour=10,
                    latest_arrival_hour=23,
                    max_duration_minutes=720,
                    connecting_airports=["DEN", "ORD"],
                    min_layover_minutes=60,
                    max_layover_minutes=240,
                    less_emissions_only=True,
                )
            ]
        )

        flight = Info.FromString(query.to_bytes()).data[0]

        self.assertEqual(flight.earliest_departure_hour, 7)
        self.assertEqual(flight.latest_departure_hour, 18)
        self.assertEqual(flight.earliest_arrival_hour, 10)
        self.assertEqual(flight.latest_arrival_hour, 23)
        self.assertEqual(flight.max_duration_minutes, 720)
        self.assertEqual(list(flight.connecting_airports), ["DEN", "ORD"])
        self.assertEqual(flight.min_layover_minutes, 60)
        self.assertEqual(flight.max_layover_minutes, 240)
        self.assertEqual(list(flight.emissions), [Emissions.LESS_EMISSIONS])

    def test_serializes_whole_search_filters(self) -> None:
        query = create_query(
            flights=[
                FlightQuery(
                    date="2099-01-02",
                    from_airport="MSP",
                    to_airport="SLC",
                )
            ],
            currency="USD",
            max_price=500,
            carry_on_bags=1,
            checked_bags=2,
            hide_separate_and_self_transfer=True,
            exclude_basic_economy=True,
        )

        info = Info.FromString(query.to_bytes())

        self.assertEqual(info.max_price, 500)
        self.assertEqual(info.baggage.carry_on_bags, 1)
        self.assertEqual(info.baggage.checked_bags, 2)
        self.assertTrue(info.hide_separate_and_self_transfer)
        self.assertTrue(info.exclude_basic_economy)


if __name__ == "__main__":
    unittest.main()
