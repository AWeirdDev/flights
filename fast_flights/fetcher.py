from typing import overload

from primp import Client
from selectolax.lexbor import LexborHTMLParser

from .integrations.base import Integration
from .parser import MetaList, parse
from .querying import Query

URL = "https://www.google.com/travel/flights"
CONSENT_SAVE_URL = "https://consent.google.com/save"


def _is_consent_page(html: str) -> bool:
    return "consent.google.com/save" in html and "Before you continue" in html


def _submit_consent(client: Client, html: str) -> None:
    """Parse the consent page, submit the 'Reject all' form so Google sets
    the SOCS cookie on the shared cookie jar, allowing retries to skip the wall.
    """
    parser = LexborHTMLParser(html)
    reject_form = None
    for form in parser.css("form"):
        inputs = {i.attributes.get("name"): i.attributes.get("value", "") for i in form.css("input")}
        # Reject-all is the form with set_eom=true and no set_sc/set_aps
        if inputs.get("set_eom") == "true" and "set_sc" not in inputs:
            reject_form = inputs
            break

    if reject_form is None:
        raise RuntimeError("Could not find consent 'Reject all' form in Google consent page")

    client.post(CONSENT_SAVE_URL, data=reject_form)


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
    html = fetch_flights_html(q, proxy=proxy, integration=integration)
    return parse(html)


def fetch_flights_html(
    q: Query | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> str:
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
        if _is_consent_page(res.text):
            _submit_consent(client, res.text)
            res = client.get(URL, params=params)
        return res.text

    else:
        return integration.fetch_html(q)
