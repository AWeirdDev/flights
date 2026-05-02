from typing import overload

from primp import Client

from .fetch_result import FetchResult
from .integrations.base import Integration
from .parser import MetaList, parse
from .querying import Query

URL = "https://www.google.com/travel/flights"


@overload
def get_flights(q: str, /, *, proxy: str | None = None) -> MetaList:
    """Get flights using a str query.

    Examples:
    - *Flights from TPE to MYJ on 2025-12-22 one way economy class*
    """


@overload
def get_flights(q: Query, /, *, proxy: str | None = None) -> MetaList:
    """Get flights using a structured query.

    Example:
    ```python
    get_flights(
        query(
            flights=[
                FlightQuery(
                    date="2025-12-22",
                    from_airport="TPE",
                    to_airport="MYJ",
                )
            ],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="",
        )
    )
    ```
    """


def get_flights(
    q: Query | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> MetaList:
    """Get flights.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
    """
    fetched = fetch_flights_html(q, proxy=proxy, integration=integration)
    flights = parse(fetched)
    if integration is not None or flights or _status(flights) == "ok":
        return flights

    if not _should_try_browser(flights):
        return flights

    try:
        from .integrations import Playwright

        browser_fetched = fetch_flights_html(q, proxy=proxy, integration=Playwright())
        browser_flights = parse(browser_fetched)
        if browser_flights or _status(browser_flights) != "no_parseable_xhr":
            return browser_flights
    except Exception:
        return flights

    return flights


def fetch_flights_html(
    q: Query | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> str | FetchResult:
    """Fetch flights and get the **HTML**.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
    """
    if integration is None:
        client = Client(
            impersonate="chrome_145",
            impersonate_os="macos",
            referer=True,
            proxy=proxy,
            cookie_store=True,
        )

        if isinstance(q, Query):
            params = q.params()

        else:
            params = {"q": q}

        res = client.get(URL, params=params)
        return res.text

    else:
        return integration.fetch_html(q)


def _status(flights: MetaList) -> str | None:
    diagnostics = getattr(flights, "diagnostics", None)
    if isinstance(diagnostics, dict):
        status = diagnostics.get("status")
        return str(status) if status is not None else None
    meta_diagnostics = getattr(getattr(flights, "metadata", None), "diagnostics", None)
    if isinstance(meta_diagnostics, dict):
        status = meta_diagnostics.get("status")
        return str(status) if status is not None else None
    return None


def _should_try_browser(flights: MetaList) -> bool:
    return _status(flights) in {
        "missing_script_ds1",
        "malformed_script_data",
        "google_error_response",
        "empty_flight_payload",
        "malformed_flight_payload",
    }
