# Lazy import Cookies to avoid heavy protobuf dependencies during import-time in tests
def get_cookies_class():
    from .cookies_impl import Cookies
    return Cookies

from .core import get_flights_from_filter, get_flights
from .filter import create_filter
from .flights_impl import Airport, FlightData, Passengers, TFSData
from .schema import Flight, Result
from .search import search_airport

__all__ = [
    "Airport",
    "TFSData",
    "create_filter",
    "FlightData",
    "Passengers",
    "get_flights_from_filter",
    "Result",
    "Flight",
    "search_airport",
    "Cookies",
    "get_flights",
]

# Backwards-compatible name: try to resolve Cookies lazily if accessed
try:
    # Provide a module-level name that will import on access
    class _CookiesProxy:
        def __getattr__(self, name):
            Cookies = get_cookies_class()
            return getattr(Cookies, name)

    Cookies = get_cookies_class()
except Exception:
    # If import fails, expose a simple proxy that will import when used
    class _CookiesProxy:
        def __getattr__(self, name):
            Cookies = get_cookies_class()
            return getattr(Cookies, name)

    Cookies = _CookiesProxy()
