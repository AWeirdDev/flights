import re
from base64 import b64encode
from datetime import datetime as Datetime
from dataclasses import dataclass
from typing import Literal, Optional, Union

from .exceptions import (
    PassengerError,
    FlightQueryError,
    ValidationError
)
from .validation import (
    validate_passengers,
    validate_flight_query,
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
        # Validate and normalize flight query parameters
        self.from_airport, self.to_airport = validate_flight_query(
            self.from_airport, 
            self.to_airport, 
            self.date, 
            self.max_stops
        )
        
        # Validate airlines if provided
        if self.airlines is not None:
            if not isinstance(self.airlines, (list, tuple)):
                raise FlightQueryError("Airlines must be a list or tuple")
            
            airlines = []
            for i, airline in enumerate(self.airlines):
                if not isinstance(airline, str):
                    raise FlightQueryError(
                        f"Airline code at index {i} must be a string, got {type(airline).__name__}"
                    )
                
                airline = airline.strip().upper()
                if not re.match(r'^[A-Z]{2}$', airline):
                    raise FlightQueryError(
                        f"Invalid airline code: '{airline}'. Must be 2 uppercase letters"
                    )
                
                airlines.append(airline)
            
            self.airlines = airlines

    def pb(self) -> FlightData:
        """Convert this query to a protobuf FlightData message.
        
        Returns:
            FlightData: The protobuf message representing this query.
        """
        if isinstance(self.date, str):
            date = self.date
        else:
            date = self.date.strftime("%Y-%m-%d")

        return FlightData(
            date=date,
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
        adults: Number of adults (16+ years). At least one adult is required when traveling with children or infants.
        children: Number of children (2-15 years).
        infants_in_seat: Number of infants (under 2 years) with their own seat.
        infants_on_lap: Number of infants (under 2 years) on an adult's lap.
        
    Raises:
        PassengerError: If the passenger configuration is invalid.
    """
    def __init__(
        self,
        *,
        adults: int = 1,  # Changed default to 1 to match DEFAULT_PASSENGERS
        children: int = 0,
        infants_in_seat: int = 0,
        infants_on_lap: int = 0,
    ):
        # Convert to integers and validate
        self.adults = int(adults) if adults is not None else 1
        self.children = int(children) if children is not None else 0
        self.infants_in_seat = int(infants_in_seat) if infants_in_seat is not None else 0
        self.infants_on_lap = int(infants_on_lap) if infants_on_lap is not None else 0
            
        # Validate passenger configuration
        validate_passengers(
            adults=self.adults,
            children=self.children,
            infants_in_seat=self.infants_in_seat,
            infants_on_lap=self.infants_on_lap
        )

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


def create_query(
    *,
    flights: list[FlightQuery],
    seat: SeatType = "economy",
    trip: TripType = "one-way",
    passengers: Optional[Passengers] = None,
    language: Union[str, Literal[""], Language] = "en-US",
    currency: Union[str, Literal[""], Currency] = "USD",
    max_stops: Optional[int] = None,
) -> Query:
    # Use default passengers if not provided
    if passengers is None:
        passengers = DEFAULT_PASSENGERS
    """Create a query for flight search.
    
    Args:
        flights: List of FlightQuery objects representing the flight segments.
        seat: Seat type (e.g., 'economy', 'business'). Defaults to 'economy'.
        trip: Type of trip ('one-way', 'round-trip', 'multi-city'). Defaults to 'one-way'.
        passengers: Passengers configuration. Defaults to 1 adult.
        language: Language code (e.g., 'en', 'es'). Empty string lets Google decide.
        currency: Currency code (e.g., 'USD', 'EUR'). Empty string lets Google decide.
        max_stops: Maximum number of stops allowed for all flights. Overrides individual flight settings.
        
    Returns:
        Query: A configured Query object ready for flight search.
        
    Raises:
        ValueError: If any of the input parameters are invalid.
        FlightQueryError: If there are issues with the flight queries.
        AirportCodeError: If any airport code is invalid.
        DateFormatError: If any date format is invalid.
        PassengerError: If passenger configuration is invalid.
    """
    # Validate required inputs
    if not isinstance(flights, (list, tuple)) or not flights:
        raise ValueError("At least one flight segment is required")
    
    if not all(isinstance(f, FlightQuery) for f in flights):
        raise ValueError("All flight segments must be FlightQuery instances")
    
    # Validate seat type
    if seat not in SEAT_LOOKUP:
        valid_seats = ", ".join(f"'{s}'" for s in SEAT_LOOKUP)
        raise ValueError(f"Invalid seat type: '{seat}'. Must be one of: {valid_seats}")
    
    # Validate trip type
    if trip not in TRIP_LOOKUP:
        valid_trips = ", ".join(f"'{t}'" for t in TRIP_LOOKUP)
        raise ValueError(f"Invalid trip type: '{trip}'. Must be one of: {valid_trips}")
    
    # Validate passengers
    if not isinstance(passengers, Passengers):
        raise ValueError("passengers must be an instance of Passengers")
    
    # Validate language
    if language and not isinstance(language, (str, Language)):
        raise ValueError("language must be a string or Language enum value")
    
    # Validate and normalize currency
    currency_code = validate_currency(currency) if currency else ""
    
    # Apply max_stops to all flights if specified
    if max_stops is not None:
        if not isinstance(max_stops, int) or max_stops < 0:
            raise ValueError("max_stops must be a non-negative integer")
        flights = [flight._setmaxstops(max_stops) for flight in flights]
    
    # Create and return the query
    return Query(
        flight_data=[flight.pb() for flight in flights],
        seat=SEAT_LOOKUP[seat],
        trip=TRIP_LOOKUP[trip],
        passengers=passengers.pb(),
        language=str(language) if language else "",
        currency=currency_code,
    )
