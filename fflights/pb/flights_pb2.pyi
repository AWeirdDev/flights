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
    def __init__(self, **kwargs): ...
    def SerializeToString(self) -> bytes: ...

class Trip(Enum):
    # UNKNOWN_TRIP = 0
    ROUND_TRIP = 1
    ONE_WAY = 2
    MULTI_CITY = 3

class Seat(Enum):
    # UNKNOWN_SEAT = 0
    ECONOMY = 1
    PREMIUM_ECONOMY = 2
    BUSINESS = 3
    FIRST = 4

class Passenger(Enum):
    # UNKNOWN_PASSENGER = 0
    ADULT = 1
    CHILD = 2
    INFANT_IN_SEAT = 3
    INFANT_ON_LAP = 4

class Airport(__Composite):
    airport: str

class FlightData(__Composite):
    date: str
    from_airport: Airport
    to_airport: Airport
    max_stops: Optional[int]
    airlines: Union[__RepeatedScalarContainer[str], list[str]]

class Info(__Composite):
    data: Union[__RepeatedCompositeContainer[FlightData], list[FlightData]]
    seat: Seat
    passengers: Union[__RepeatedCompositeContainer[Passenger], list[Passenger]]
    trip: Trip
