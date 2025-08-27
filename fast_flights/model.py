from dataclasses import dataclass
from typing import Annotated, Literal, Union


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
    duration: Annotated[int, "(minutes)"]
    plane_type: str


@dataclass
class CarbonEmission:
    typical_on_route: Annotated[int, "(grams)"]
    emission: Annotated[int, "(grams)"]


@dataclass
class Flights:
    type: Union[str, Literal["multi"]]
    price: int
    airlines: list[str]
    flights: list[SingleFlight]
    carbon: CarbonEmission
