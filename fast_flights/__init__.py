from . import integrations
from .exceptions import FastFlightsError, APIError
from .querying import FlightQuery, Passengers, create_query
from .fetcher import get_flights, fetch_flights_html

# Create alias for backward compatibility
create_filter = create_query

__all__ = [
    # Core functionality
    "FlightQuery",
    "Passengers",
    "create_query",
    "create_filter",
    "get_flights",
    "fetch_flights_html",
    "integrations",
    
    # Public exceptions
    "FastFlightsError",
    "APIError"
]
