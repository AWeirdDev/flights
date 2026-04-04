from typing import Literal, overload

from primp import Client

from .integrations.base import Integration
from .parser import MetaList, parse
from .querying import Query

URL = "https://www.google.com/travel/flights"


@overload
def get_flights(
    q: str,
    /,
    *,
    proxy: str | None = None,
    return_url: Literal[False] = False,
) -> MetaList:
    """Get flights using a str query.

    Examples:
    - *Flights from TPE to MYJ on 2025-12-22 one way economy class*
    """


@overload
def get_flights(
    q: str,
    /,
    *,
    proxy: str | None = None,
    return_url: Literal[True],
) -> tuple[MetaList, str]:
    """Get flights using a str query, returning both flights and URL.

    Examples:
    - *Flights from TPE to MYJ on 2025-12-22 one way economy class*
    """


@overload
def get_flights(
    q: Query,
    /,
    *,
    proxy: str | None = None,
    return_url: Literal[False] = False,
) -> MetaList:
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


@overload
def get_flights(
    q: Query,
    /,
    *,
    proxy: str | None = None,
    return_url: Literal[True],
) -> tuple[MetaList, str]:
    """Get flights using a structured query, returning both flights and URL.

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
        ),
        return_url=True
    )
    ```
    """


def get_flights(
    q: Query | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
    return_url: bool = False,
) -> MetaList | tuple[MetaList, str]:
    """Get flights.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
        return_url (bool, optional): If True, returns a tuple of (MetaList, url).
            If False (default), returns only MetaList for backward compatibility.
    
    Returns:
        MetaList if return_url is False (default), or
        tuple of (MetaList, url) if return_url is True.
    """
    html, url = fetch_flights_html(q, proxy=proxy, integration=integration)
    flights = parse(html)
    
    if return_url:
        return flights, url
    return flights


def fetch_flights_html(
    q: Query | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> tuple[str, str]:
    """Fetch flights and get the **HTML** and **URL**.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
    
    Returns:
        A tuple of (html, url) where html is the response text
        and url is the final URL of the request.
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
        return res.text, str(res.url)

    else:
        html = integration.fetch_html(q)
        return html, URL
