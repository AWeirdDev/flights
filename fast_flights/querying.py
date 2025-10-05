import re
from base64 import b64encode
from datetime import datetime as Datetime
from dataclasses import dataclass
from typing import Literal, Optional, TypeVar, Union, get_args, get_origin

from .exceptions import (
    PassengerError,
    FlightQueryError,
)
from .validation import (
    validate_passengers,
    validate_flight_query,
    validate_seat_type,
    validate_trip_type,
    validate_flights_list,
    validate_airlines,
    validate_max_stops,
    validate_and_normalize_date,
    validate_language,
    validate_currency
)

from .types import Currency, Language, SeatType, TripType
from .pb.flights_pb2 import Airport, Info, Passenger, Seat, FlightData, Trip


@dataclass
class Query:
    """A query containing `?tfs` data."""

    flight_data: list[FlightData]
    seat: Seat
    trip: Trip
    passengers: list[Passenger]
    language: str
    currency: str
    
    def __str__(self) -> str:
        """Return a human-readable string representation of the query."""
        flight_info = []
        for i, flight in enumerate(self.flight_data, 1):
            flight_info.append(f"  Flight {i}:")
            flight_info.append(f"    From: {flight.from_airport.airport if flight.HasField('from_airport') else 'N/A'}")
            flight_info.append(f"    To: {flight.to_airport.airport if flight.HasField('to_airport') else 'N/A'}")
            flight_info.append(f"    Date: {flight.date}")
            
            if flight.airlines:
                flight_info.append(f"    Airlines: {', '.join(flight.airlines)}")
            
            if flight.HasField('max_stops'):
                flight_info.append(f"    Max Stops: {flight.max_stops}")
        
        # Count passenger types
        passenger_counts = {}
        for p in self.passengers:
            if p == Passenger.ADULT:
                passenger_counts['Adults'] = passenger_counts.get('Adults', 0) + 1
            elif p == Passenger.CHILD:
                passenger_counts['Children'] = passenger_counts.get('Children', 0) + 1
            elif p in (Passenger.INFANT_IN_SEAT, Passenger.INFANT_ON_LAP):
                passenger_counts['Infants'] = passenger_counts.get('Infants', 0) + 1
        
        return (
            f"Query Details:\n"
            f"Seat Class: {self.seat}\n"
            f"Trip Type: {self.trip}\n"
            f"Passengers: {', '.join(f'{count} {type_}' for type_, count in passenger_counts.items() if count > 0)}\n"
            f"Language: {self.language or 'Default'}\n"
            f"Currency: {self.currency or 'Default'}\n"
            f"Flights:\n" + '\n'.join(flight_info)
        )

    def to_proto(self) -> Info:
        """(internal) Protobuf data. (`Info`)"""
        return Info(
            data=self.flight_data,
            seat=self.seat,
            trip=self.trip,
            passengers=self.passengers,
        )

    def to_bytes(self) -> bytes:
        """Convert this query to bytes."""
        return self.to_proto().SerializeToString()

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
    """Represents a flight search query.
    
    Args:
        date: Departure date as a string in YYYY-MM-DD format or a datetime object.
        from_airport: IATA code of the departure airport (e.g., 'JFK', 'LAX').
        to_airport: IATA code of the arrival airport (e.g., 'SFO', 'LHR').
        max_stops: Maximum number of stops allowed (None for any number of stops).
        airlines: Optional list of airline IATA codes to filter by.
        
    Raises:
        FlightQueryError: If any of the query parameters are invalid.
    """
    date: Union[str, Datetime]
    from_airport: str
    to_airport: str
    max_stops: Optional[int] = None
    airlines: Optional[list[str]] = None

    def __post_init__(self):
        """Validate and normalize flight query parameters after initialization.
        
        Raises:
            AirportCodeError: If airport codes are invalid
            DateFormatError: If date format is invalid
            FlightQueryError: For other validation errors
        """
        # Validate and normalize date first
        self._normalized_date = validate_and_normalize_date(self.date)
        
        # Validate and normalize flight query parameters
        self.from_airport, self.to_airport = validate_flight_query(
            self.from_airport, 
            self.to_airport, 
            self._normalized_date, 
            self.max_stops
        )
        
        # Validate and normalize airlines if provided
        if self.airlines is not None:
            try:
                self.airlines = validate_airlines(self.airlines)
            except ValueError as e:
                raise FlightQueryError(str(e)) from e

    def to_proto(self) -> FlightData:
        """Convert this query to a protobuf FlightData message.
        
        Returns:
            FlightData: The protobuf message representing this query.
            
        Note:
            All validations should be done in __post_init__.
            This method should only convert already validated data to protobuf.
        """
        return FlightData(
            date=self._normalized_date,
            from_airport=Airport(airport=self.from_airport),
            to_airport=Airport(airport=self.to_airport),
            max_stops=self.max_stops if self.max_stops is not None else None,
            airlines=self.airlines if self.airlines else None,
        )

    def _setmaxstops(self, m: Optional[int] = None) -> "FlightQuery":
        if m is not None:
            self.max_stops = m

        return self


class Passengers:
    """Represents a group of passengers for a flight.
    
    Args:
        adults: Number of adults (16+ years). At least one adult is required.
        children: Number of children (2-15 years).
        infants_in_seat: Number of infants (under 2 years) with their own seat.
        infants_on_lap: Number of infants (under 2 years) on an adult's lap.
        
    Raises:
        PassengerError: If the passenger configuration is invalid.
    """
    adults: int
    children: int
    infants_in_seat: int
    infants_on_lap: int
    
    def __init__(
        self,
        *,
        adults: int = 1,
        children: int = 0,
        infants_in_seat: int = 0,
        infants_on_lap: int = 0,
    ) -> None:
        """Initialize and validate passenger configuration."""
        self.adults = int(adults)
        self.children = int(children)
        self.infants_in_seat = int(infants_in_seat)
        self.infants_on_lap = int(infants_on_lap)
            
        validate_passengers(
            adults=self.adults,
            children=self.children,
            infants_in_seat=self.infants_in_seat,
            infants_on_lap=self.infants_on_lap
        )

    def to_proto(self) -> list[Passenger]:
        return [
            *(Passenger.ADULT for _ in range(self.adults)),
            *(Passenger.CHILD for _ in range(self.children)),
            *(Passenger.INFANT_IN_SEAT for _ in range(self.infants_in_seat)),
            *(Passenger.INFANT_ON_LAP for _ in range(self.infants_on_lap)),
        ]


from typing import TypeVar, Type, Any, get_origin, get_args, cast

T = TypeVar('T')

def _get_literal_values(tp: Any) -> tuple[str, ...]:
    """Extract the literal values from a Literal type.
    
    Returns:
        tuple[str, ...]: The literal values as strings, or empty tuple if not a Literal
    """
    origin = get_origin(tp)
    if origin is not Literal:
        return ()
    
    args = get_args(tp)
    if not args:
        return ()
        
    # Filter out non-string values and ensure they're strings
    return tuple(str(arg) for arg in args if isinstance(arg, (str, int, bool, float)))

def _create_enum_lookup(enum_type: Union[Type[T], Type[str]], literal_type: Any) -> dict[str, T]:
    """Create a lookup dictionary from a Literal type to an enum or string type.
    
    Args:
        enum_type: The target type (e.g., Seat, Trip, or str for direct mappings)
        literal_type: The Literal type (e.g., SeatType, TripType, Language, Currency)
        
    Returns:
        dict[str, T]: A mapping from string literals to enum values or strings of type T
    """
    # Get the allowed string values from the Literal type
    literal_values = _get_literal_values(literal_type)
    if not literal_values:
        return {}
    
    # If the target type is str, create a direct mapping (for Language and Currency)
    if enum_type is str:
        return {value: value for value in literal_values if isinstance(value, str)}
    
    # For enum types, map string values to enum values
    lookup: dict[str, T] = {}
    for value in literal_values:
        if not isinstance(value, str):
            continue
            
        # Convert string like "premium-economy" to "PREMIUM_ECONOMY"
        enum_name = value.upper().replace('-', '_')
        try:
            enum_value = getattr(enum_type, enum_name)
            lookup[value] = enum_value
        except AttributeError:
            continue  # Skip if the enum value doesn't exist
            
    return lookup

# Create lookups from Literal types to their corresponding values
SEAT_LOOKUP = _create_enum_lookup(Seat, SeatType)
TRIP_LOOKUP = _create_enum_lookup(Trip, TripType)
LANGUAGE_LOOKUP = _create_enum_lookup(str, Language)
CURRENCY_LOOKUP = _create_enum_lookup(str, Currency)

# Runtime validation of the lookup tables
def _validate_lookup(lookup: dict, type_name: str, expected_values: set) -> None:
    """Validate that all expected values are present in the lookup."""
    missing = expected_values - set(lookup.keys())
    if missing:
        raise RuntimeError(f"Missing {type_name} values for: {', '.join(sorted(missing))}")

# Validate all lookups
_validate_lookup(SEAT_LOOKUP, "Seat", set(get_args(SeatType)))
_validate_lookup(TRIP_LOOKUP, "Trip", set(get_args(TripType)))
_validate_lookup(LANGUAGE_LOOKUP, "Language", set(get_args(Language)))
_validate_lookup(CURRENCY_LOOKUP, "Currency", set(get_args(Currency)))


def create_query(
    *,
    flights: list[FlightQuery],
    seat: SeatType = "economy",
    trip: TripType = "one-way",
    passengers: Passengers = Passengers(),
    language: Union[str, Literal[""], Language] = "en-US",
    currency: Union[str, Literal[""], Currency] = "USD",
    max_stops: Optional[int] = None,
) -> Query:
    """Create a query for flight search.
    
    Args:
        flights: List of FlightQuery objects representing the flight segments.
            Must contain at least one flight.
        seat: Seat type (e.g., 'economy', 'business'). Defaults to 'economy'.
        trip: Type of trip ('one-way', 'round-trip', 'multi-city'). 
            Defaults to 'one-way'.
        passengers: Passengers configuration. If None, defaults to 1 adult.
        language: Language code (e.g., 'en-US', 'es'). Empty string lets Google decide.
        currency: Currency code (e.g., 'USD', 'EUR'). Empty string lets Google decide.
        max_stops: Maximum number of stops allowed for all flights. 
            Overrides individual flight settings. Use None for no limit.
        
    Returns:
        Query: A configured Query object ready for flight search.
        
    Raises:
        FlightQueryError: If there are issues with the flight queries.
        ValueError: If any of the input parameters are invalid.
        AirportCodeError: If any airport code is invalid.
        DateFormatError: If any date format is invalid.
        PassengerError: If passenger configuration is invalid.
        
    Example:
        >>> query = create_query(
        ...     flights=[
        ...         FlightQuery(
        ...             date="2025-12-25",
        ...             from_airport="JFK",
        ...             to_airport="LAX"
        ...         )
        ...     ],
        ...     passengers=Passengers(adults=2, children=1)
        ... )
    """
    
    # Validate passengers
    if not isinstance(passengers, Passengers):
        raise ValueError("passengers must be an instance of Passengers")
    
    # Validate language
    language = validate_language(language) if language else ""
    language = LANGUAGE_LOOKUP.get(language, "") if language else ""
    
    # Validate currency
    if currency:
        currency = validate_currency(currency)
    currency_code = CURRENCY_LOOKUP.get(currency, "") if currency else ""
    
    # Validate flights list
    validate_flights_list(flights, FlightQuery)
    
    # Validate and normalize seat type
    seat = validate_seat_type(seat)
    
    # Validate and normalize trip type
    trip = validate_trip_type(trip)
    
    # Validate and apply max_stops to all flights if specified
    if max_stops is not None:
        max_stops = validate_max_stops(max_stops)
        flights = [flight._setmaxstops(max_stops) for flight in flights]
    
    # Create and return the query
    return Query(
        flight_data=[flight.to_proto() for flight in flights],
        seat=SEAT_LOOKUP[seat],
        trip=TRIP_LOOKUP[trip],
        passengers=passengers.to_proto(),
        language=language,
        currency=currency_code,
    )
