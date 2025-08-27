from .querying import (
    FlightQuery,
    Query,
    Passengers,
    create_query,
    create_query as create_filter,  # alias
)
from .fetcher import get_flights, fetch_flights_html

__all__ = [
    "FlightQuery",
    "Query",
    "Passengers",
    "create_query",
    "create_filter",
    "get_flights",
    "fetch_flights_html",
]
