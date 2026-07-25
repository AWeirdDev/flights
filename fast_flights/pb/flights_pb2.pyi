from enum import Enum
from typing import Generic, Iterable, Optional, TypeVar, Union

T = TypeVar("T")

class __RepeatedCompositeContainer(Generic[T]):
    def add(self) -> T: ...
    def append(self, o: T) -> None: ...
    def extend(self, it: Iterable[T]) -> None: ...
    def clear(self) -> None: ...

class __RepeatedScalarContainer(Generic[T]):
    def append(self, o: T) -> None: ...
    def extend(self, it: Iterable[T]) -> None: ...
    def clear(self) -> None: ...

class __Composite:
    def __init__(self, **kwargs) -> None: ...
    def SerializeToString(self) -> bytes: ...

class Trip(int, Enum):
    # UNKNOWN_TRIP = 0
    ROUND_TRIP = 1
    ONE_WAY = 2
    MULTI_CITY = 3

class Seat(int, Enum):
    # UNKNOWN_SEAT = 0
    ECONOMY = 1
    PREMIUM_ECONOMY = 2
    BUSINESS = 3
    FIRST = 4

class Passenger(int, Enum):
    # UNKNOWN_PASSENGER = 0
    ADULT = 1
    CHILD = 2
    INFANT_IN_SEAT = 3
    INFANT_ON_LAP = 4

class Emissions(int, Enum):
    # UNKNOWN_EMISSIONS = 0
    LESS_EMISSIONS = 1

class Airport(__Composite):
    airport: str

class FlightData(__Composite):
    date: str
    from_airport: Airport
    to_airport: Airport
    max_stops: int | None
    airlines: __RepeatedScalarContainer[str] | list[str]
    earliest_departure_hour: int | None
    latest_departure_hour: int | None
    earliest_arrival_hour: int | None
    latest_arrival_hour: int | None
    max_duration_minutes: int | None
    connecting_airports: __RepeatedScalarContainer[str] | list[str]
    min_layover_minutes: int | None
    max_layover_minutes: int | None
    emissions: __RepeatedScalarContainer[Emissions] | list[Emissions]

class Baggage(__Composite):
    carry_on_bags: int | None
    checked_bags: int | None

class Info(__Composite):
    data: __RepeatedCompositeContainer[FlightData] | list[FlightData]
    seat: Seat
    passengers: __RepeatedCompositeContainer[Passenger] | list[Passenger]
    max_price: int | None
    baggage: Baggage
    hide_separate_and_self_transfer: bool | None
    trip: Trip
    exclude_basic_economy: bool | None
