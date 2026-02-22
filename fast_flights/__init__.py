from . import integrations

from .querying import (
    FlightQuery,
    Query,
    Passengers,
    create_query,
    create_query as create_filter,  # alias
)
from .fetcher import get_flights, fetch_flights_html
from .hotels import get_hotels
from .hotels_schema import Hotel, HotelResult

__all__ = [
    "FlightQuery",
    "Query",
    "Passengers",
    "create_query",
    "create_filter",
    "get_flights",
    "fetch_flights_html",
    "integrations",
    "get_hotels",
    "Hotel",
    "HotelResult",
]
