"""Typed implementation of flights_pb2.py"""

import base64
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Literal, Optional, Union

from . import flights_pb2 as PB
from ._generated_enum import Airport
from .types import Passengers

if TYPE_CHECKING:
    PB: Any


@dataclass
class FlightData:
    """Represents flight data.

    Args:
        date (str): Date.
        from_airport (str): Departure (airport). Where from?
        to_airport (str): Arrival (airport). Where to?
        max_stops (int, optional): Maximum number of stops. Default is None.
    """

    __slots__ = ("date", "from_airport", "to_airport", "max_stops")
    date: str
    from_airport: str
    to_airport: str
    max_stops: Optional[int]

    def __init__(
        self,
        *,
        date: str,
        from_airport: Union[Airport, str],
        to_airport: Union[Airport, str],
        max_stops: Optional[int] = None,
    ):
        self.date = date
        self.from_airport = (
            from_airport.value if isinstance(from_airport, Airport) else from_airport
        )
        self.to_airport = (
            to_airport.value if isinstance(to_airport, Airport) else to_airport
        )
        self.max_stops = max_stops

    def attach(self, info: PB.Info) -> None:  # type: ignore
        data = info.data.add()
        data.date = self.date
        data.from_flight.airport = self.from_airport
        data.to_flight.airport = self.to_airport
        if self.max_stops is not None:
            data.max_stops = self.max_stops

    def __repr__(self) -> str:
        return (
            f"FlightData(date={self.date!r}, "
            f"from_airport={self.from_airport}, "
            f"to_airport={self.to_airport}, "
            f"max_stops={self.max_stops})"
        )


@dataclass
class TFSData:
    """``?tfs=`` data. (internal)

    Use `TFSData.from_interface` instead.
    """

    flight_data: List[FlightData]
    trip: int  # Use int for protobuf enum values
    seat: int  # Use int for protobuf enum values
    passengers: Passengers
    max_stops: Optional[int] = None

    def pb(self) -> PB.Info:  # type: ignore
        info = PB.Info()
        info.seat = self.seat
        info.trip = self.trip

        self.passengers.attach(info)

        for fd in self.flight_data:
            fd.attach(info)

        # If max_stops is set, attach it to all flight data entries
        if self.max_stops is not None:
            for flight in info.data:
                flight.max_stops = self.max_stops

        return info

    def to_string(self) -> bytes:
        return self.pb().SerializeToString()

    def as_b64(self) -> bytes:
        return base64.b64encode(self.to_string())

    @staticmethod
    def from_interface(
        *,
        flight_data: List[FlightData],
        trip: Literal["round-trip", "one-way", "multi-city"],
        passengers: Passengers,
        seat: Literal["economy", "premium-economy", "business", "first"],
        max_stops: Optional[int] = None,
    ) -> "TFSData":
        """Use ``?tfs=`` from an interface.

        Args:
            flight_data (list[FlightData]): Flight data as a list.
            trip ("one-way" | "round-trip" | "multi-city"): Trip type.
            passengers (Passengers): Passengers.
            seat ("economy" | "premium-economy" | "business" | "first"): Seat.
            max_stops (int, optional): Maximum number of stops.
        """
        trip_t = {
            "round-trip": 1,  # ROUND_TRIP
            "one-way": 0,  # ONE_WAY
            "multi-city": 2,  # MULTI_CITY
        }[trip]
        seat_t = {
            "economy": 0,  # ECONOMY
            "premium-economy": 1,  # PREMIUM_ECONOMY
            "business": 2,  # BUSINESS
            "first": 3,  # FIRST
        }[seat]

        return TFSData(
            flight_data=flight_data,
            seat=seat_t,
            trip=trip_t,
            passengers=passengers,
            max_stops=max_stops,
        )

    def __repr__(self) -> str:
        return (
            f"TFSData(flight_data={self.flight_data!r}, max_stops={self.max_stops!r})"
        )


def create_filter(
    flight_data: List[FlightData],
    trip: Literal["round-trip", "one-way", "multi-city"],
    seat: Literal["economy", "premium-economy", "business", "first"],
    passengers: Passengers,
    max_stops: Optional[int] = None,
) -> TFSData:
    """Create a filter for flight search"""
    # Convert string values to proper enum values
    trip_t = {
        "round-trip": 1,  # ROUND_TRIP
        "one-way": 0,  # ONE_WAY
        "multi-city": 2,  # MULTI_CITY
    }[trip]
    seat_t = {
        "economy": 0,  # ECONOMY
        "premium-economy": 1,  # PREMIUM_ECONOMY
        "business": 2,  # BUSINESS
        "first": 3,  # FIRST
    }[seat]

    return TFSData(
        flight_data=flight_data,
        trip=trip_t,
        seat=seat_t,
        passengers=passengers,
        max_stops=max_stops,
    )
