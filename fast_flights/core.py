import re
import json
from typing import Any, Optional

import requests
from selectolax.lexbor import LexborHTMLParser, LexborNode

from .flights_impl import TFSData
from .schema import Flight, FlightResults

ua = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0"
)


def request_flights(
    tfs: TFSData,
    *,
    currency: Optional[str] = None,
    language: Optional[str],
    **kwargs: Any,
) -> requests.Response:
    r = requests.get(
        "https://www.google.com/travel/flights",
        params={
            "tfs": tfs.as_b64(),
            "hl": language,
            "tfu": "EgQIABABIgA",  # show all flights and prices condition
            "curr": currency,
        },
        headers={"user-agent": ua, "accept-language": "en"},
        **kwargs,
    )
    r.raise_for_status()
    return r


def parse_response(r: requests.Response) -> FlightResults:
    flights = []

    match = re.search(r'hash: \'9\', data:(\[.*?\]), sideChannel: {', r.text)
    assert match, 'Cannot find flight data in script tag'
    json_data = json.loads(match.group(1))

    return FlightResults.parse(json_data)


def get_flights(
    tfs: TFSData,
    *,
    currency: Optional[str] = None,
    language: Optional[str] = None,
    cookies: Optional[dict] = None,
    attempted: bool = False,
    **kwargs: Any,
) -> FlightResults:
    rs = request_flights(tfs, currency=currency, language=language, **kwargs)
    results = parse_response(rs)

    if not [*results.best, *results.other]:
        if not attempted:
            return get_flights(
                tfs,
                cookies=cookies,
                attempted=True,
                **kwargs,
            )

        raise RuntimeError(
            "No flights found. (preflight checked)\n"
            "Possible reasons:\n"
            "- Invalid query (e.g., date is in the past or cannot be booked)\n"
            "- Invalid airport"
        )

    return results
