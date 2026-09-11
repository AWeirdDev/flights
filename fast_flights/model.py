from dataclasses import dataclass
from typing import Literal


@dataclass
class Airline:
    code: str
    name: str


@dataclass
class Alliance:
    code: str
    name: str


@dataclass
class JsMetadata:
    airlines: list[Airline]
    alliances: list[Alliance]


@dataclass
class Airport:
    name: str
    code: str


@dataclass
class SimpleDatetime:
    date: tuple[int, int, int]
    time: tuple[int, int]


@dataclass
class SingleFlight:
    from_airport: Airport
    to_airport: Airport
    departure: SimpleDatetime
    arrival: SimpleDatetime

    duration: int
    """Unit: minutes"""

    plane_type: str


@dataclass
class CarbonEmission:
    typical_on_route: int
    """Unit: grams"""

    emission: int
    """Unit: grams"""


@dataclass
class Flights:
    type: str | Literal["multi"]
    price: int | None
    """Fare amount, or None when Google returns an unpriced itinerary."""
    airlines: list[str]
    flights: list[SingleFlight]
    carbon: CarbonEmission
