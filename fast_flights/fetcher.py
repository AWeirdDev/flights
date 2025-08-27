from typing import Optional, Union, overload

from primp import Client

from .querying import Query
from .parser import MetaList, parse

URL = "https://www.google.com/travel/flights"


@overload
def get_flights(q: str, /, *, proxy: Optional[str] = None):
    """Get flights using a str query.

    Examples:
    - *Flights from TPE to MYJ on 2025-12-22 one way economy class*
    """


@overload
def get_flights(q: Query, /, *, proxy: Optional[str] = None):
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


def get_flights(q: Union[Query, str], /, *, proxy: Optional[str] = None) -> MetaList:
    """Get flights.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
    """
    html = fetch_flights_html(q, proxy=proxy)
    return parse(html)


def fetch_flights_html(q: Union[Query, str], /, *, proxy: Optional[str] = None) -> str:
    """Fetch flights and get the **HTML**.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
    """
    client = Client(
        impersonate="chrome_133",
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
