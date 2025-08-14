from base64 import b64encode
from dataclasses import dataclass
from typing import Annotated, Literal, Optional, Tuple, Union
from typing_extensions import Unpack

from .types import Currency, Language, SeatType, TripType
from .pb.flights_pb2 import Airport, Info, Passenger, Seat, FlightData, Trip

# Provided by @lookacat (issue: #59)
StrQuerySimple = Tuple[
    Annotated[str, "From"],
    Annotated[str, "To"],
    Annotated[str, "Date"],
    Annotated[TripType, "Trip type"],
    Annotated[SeatType, "Seat type"],
]
LangAndCurr = Tuple[
    Annotated[Union[Literal[""], Language, str], "Language"],
    Annotated[Union[Literal[""], Currency, str], "Currency"],
]
StrQueryAdvanced = Tuple[Unpack[StrQuerySimple], Unpack[LangAndCurr]]
StrQueryCustom = Tuple[str, Unpack[LangAndCurr]]

StrQuery = Union[StrQuerySimple, StrQueryAdvanced, StrQueryCustom]


@dataclass
class StrQueryHolder:
    q: str
    language: str
    currency: str

    def params(self) -> dict[str, str]:
        return {"q": self.q, "hl": self.language, "curr": self.currency}


def str_query(t: StrQuery) -> StrQueryHolder:
    """Create a str-based query from a tuple.

    Example:

    ```python
    # custom (recommended)
    str_query((
        "Flights from TPE to MYJ on 2025-12-22 one way economy class",
        "en-US",
        "USD"
    ))

    # simple (not really)
    str_query((
        "TPE",  # from
        "MYJ",  # to
        "2025-12-22",  # date
        "one-way",  # trip type
        "economy",  # seat type
    ))

    # + language & currency
    str_query((
        "TPE",  # from
        "MYJ",  # to
        "2025-12-22",  # date
        "one-way",  # trip type
        "economy",  # seat type

        "en-US",  # language
        "USD"  # currency
    ))
    ```
    """

    if len(t) == 5:
        return StrQueryHolder(
            q=f"Flights to {t[1]} from {t[0]} on {t[2]} {t[3].replace('-', ' ')} {t[4].replace('-', ' ')} class",
            language="",
            currency="",
        )

    elif len(t) == 7:
        return StrQueryHolder(
            f"Flights to {t[1]} from {t[0]} on {t[2]} {t[3].replace('-', ' ')} {t[4].replace('-', ' ')} class",
            language=t[5],
            currency=t[6],
        )

    elif len(t) == 3:
        return StrQueryHolder(t[0], language=t[1], currency=t[2])

    raise RuntimeError("unreachable! (unknown str query base)")


@dataclass
class Query:
    """A query containing `?tfs` data."""

    flight_data: list[FlightData]
    seat: Seat
    trip: Trip
    passengers: list[Passenger]
    language: str
    currency: str

    def pb(self) -> Info:
        """(internal) Protobuf data. (`Info`)"""
        return Info(
            data=self.flight_data,
            seat=self.seat,
            trip=self.trip,
            passengers=self.passengers,
        )

    def to_bytes(self) -> bytes:
        """Convert this query to bytes."""
        return self.pb().SerializeToString()

    def to_str(self) -> str:
        """Convert this query to a string."""
        return b64encode(self.to_bytes()).decode("utf-8")

    def url(self) -> str:
        """Get the URL for this query.

        This is generally used for debugging purposes.
        """
        return (
            "https://www.google.com/travel/flights/search?tfs="
            + self.to_str()
            + "&hl="
            + self.language
            + "&curr="
            + self.currency
        )

    def params(self) -> dict[str, str]:
        """Create `params` in dictionary form."""
        return {"tfs": self.to_str(), "hl": self.language, "curr": self.currency}

    def __repr__(self) -> str:
        return "Query(...)"


@dataclass
class FlightQuery:
    date: str
    from_airport: str
    to_airport: str
    max_stops: Optional[int] = None
    airlines: Optional[list[str]] = None

    def pb(self) -> FlightData:
        return FlightData(
            date=self.date,
            from_airport=Airport(airport=self.from_airport),
            to_airport=Airport(airport=self.to_airport),
            max_stops=self.max_stops,
            airlines=self.airlines,
        )

    def _setmaxstops(self, m: Optional[int] = None) -> "FlightQuery":
        if m is not None:
            self.max_stops = m

        return self


class Passengers:
    def __init__(
        self,
        *,
        adults: int = 0,
        children: int = 0,
        infants_in_seat: int = 0,
        infants_on_lap: int = 0,
    ):
        assert (
            sum((adults, children, infants_in_seat, infants_on_lap)) <= 9
        ), "Too many passengers (> 9)"
        assert (
            infants_on_lap <= adults
        ), "Must have at least one adult per infant on lap"

        self.adults = adults
        self.children = children
        self.infants_in_seat = infants_in_seat
        self.infants_on_lap = infants_on_lap

    def pb(self) -> list[Passenger]:
        return [
            *(Passenger.ADULT for _ in range(self.adults)),
            *(Passenger.CHILD for _ in range(self.children)),
            *(Passenger.INFANT_IN_SEAT for _ in range(self.infants_in_seat)),
            *(Passenger.INFANT_ON_LAP for _ in range(self.infants_on_lap)),
        ]


DEFAULT_PASSENGERS = Passengers(adults=1)
SEAT_LOOKUP = {
    "economy": Seat.ECONOMY,
    "premium-economy": Seat.PREMIUM_ECONOMY,
    "business": Seat.BUSINESS,
    "first": Seat.FIRST,
}
TRIP_LOOKUP = {
    "round-trip": Trip.ROUND_TRIP,
    "one-way": Trip.ONE_WAY,
    "multi-city": Trip.MULTI_CITY,
}


def query(
    *,
    flights: list[FlightQuery],
    seat: SeatType = "economy",
    trip: TripType = "one-way",
    passengers: Passengers = DEFAULT_PASSENGERS,
    language: Union[str, Literal[""], Language] = "",
    currency: Union[str, Literal[""], Currency] = "",
    max_stops: Optional[int] = None,
) -> Query:
    """Create a query.

    Args:
        flights: The flight queries.
        seat: Desired seat type.
        trip: Trip type.
        passengers: Passengers.
        language: Set the language. Use `""` (blank str) to let Google decide.
        currency: Set the currency. Use `""` (blank str) to let Google decide.
        max_stops (optional): Set the maximum stops for every flight query, if present.
    """
    return Query(
        flight_data=[flight._setmaxstops(max_stops).pb() for flight in flights],
        seat=SEAT_LOOKUP[seat],
        trip=TRIP_LOOKUP[trip],
        passengers=passengers.pb(),
        language=language,
        currency=currency,
    )
