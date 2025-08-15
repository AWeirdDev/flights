from typing import Optional, Union, overload
from primp import Client

from .querying import Query, StrQuery, StrQueryHolder, str_query
from .parser import MetaList, parse

URL = "https://www.google.com/travel/flights"


@overload
def get_flights(q: str, /, *, proxy: Optional[str] = None):
    """Get flights using a str query.

    Examples:
    - *Flights from TPE to MYJ on 2025-12-22 one way economy class*
    """


@overload
def get_flights(q: StrQuery, /, *, proxy: Optional[str] = None):
    """Get flights using a tuple.

    # q
    Create a str-based query from a tuple.

    Example:

    ```python
    # custom (recommended)
    (
        "Flights from TPE to MYJ on 2025-12-22 one way economy class",
        "en-US",
        "USD"
    )

    # simple (not really)
    (
        "TPE",  # from
        "MYJ",  # to
        "2025-12-22",  # date
        "one-way",  # trip type
        "economy",  # seat type
    )

    # + language & currency
    (
        "TPE",  # from
        "MYJ",  # to
        "2025-12-22",  # date
        "one-way",  # trip type
        "economy",  # seat type

        "en-US",  # language
        "USD"  # currency
    )
    ```
    """


@overload
def get_flights(q: StrQueryHolder, /, *, proxy: Optional[str] = None):
    """Get flights using `str_query()`.

    # q
    Create a str-based query from a tuple, using the `str_query()` function.

    Example:

    ```python
    # custom (recommended)
    str_query((
        "Flights from TPE to MYJ on 2025-12-22 one way economy class",
        "en-US",
        "USD"
    ))

    # simple (not really)
    str_query((
        "TPE",  # from
        "MYJ",  # to
        "2025-12-22",  # date
        "one-way",  # trip type
        "economy",  # seat type
    ))

    # + language & currency
    str_query((
        "TPE",  # from
        "MYJ",  # to
        "2025-12-22",  # date
        "one-way",  # trip type
        "economy",  # seat type

        "en-US",  # language
        "USD"  # currency
    ))
    ```
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


def get_flights(
    q: Union[Query, StrQuery, StrQueryHolder, str], /, *, proxy: Optional[str] = None
) -> MetaList:
    """Get flights.

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

    elif isinstance(q, tuple):
        # StrQuery
        params = str_query(q).params()

    elif isinstance(q, StrQueryHolder):
        params = q.params()

    else:
        params = {"q": q}

    res = client.get(URL, params=params)
    return parse(res.text)
