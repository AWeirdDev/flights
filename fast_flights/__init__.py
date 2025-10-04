from . import integrations
from .exceptions import (
    FastFlightsError,
    ValidationError,
    AirportCodeError,
    DateFormatError,
    PassengerError,
    FlightQueryError,
    APIConnectionError,
    APIError,
)
from .validation import (
    validate_airport_code,
    validate_date,
    validate_passengers,
    validate_flight_query,
    validate_currency,
)
from .querying import (
    FlightQuery,
    Query,
    Passengers,
    create_query,
    create_query as create_filter,  # alias
)
from .fetcher import get_flights, fetch_flights_html

__all__ = [
    # Core functionality
    "FlightQuery",
    "Query",
    "Passengers",
    "create_query",
    "create_filter",
    "get_flights",
    "fetch_flights_html",
    "integrations",
    
    # Exceptions
    "FastFlightsError",
    "ValidationError",
    "AirportCodeError",
    "DateFormatError",
    "PassengerError",
    "FlightQueryError",
    "APIConnectionError",
    "APIError",
    
    # Validation utilities
    "validate_airport_code",
    "validate_date",
    "validate_passengers",
    "validate_flight_query",
    "validate_currency",
]
