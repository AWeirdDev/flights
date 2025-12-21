import re
import json
from typing import List, Literal, Optional, Union

from selectolax.lexbor import LexborHTMLParser, LexborNode

from .decoder import DecodedResult, ResultDecoder
from .schema import Flight, Result
from .flights_impl import FlightData, Passengers
from .filter import TFSData
from .fallback_playwright import fallback_playwright_fetch
from .bright_data_fetch import bright_data_fetch
from .primp import Client, Response


DataSource = Literal['html', 'js']

# Default cookies embedded into the app to help bypass common consent gating.
# These are used only if the caller does not supply cookies (binary) and
# does not provide cookies via request_kwargs.
_DEFAULT_COOKIES = {
    "CONSENT": "PENDING+987",
    "SOCS": "CAESHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmRlIAEaBgiAo_CmBg",
}
_DEFAULT_COOKIES_BYTES = json.dumps(_DEFAULT_COOKIES).encode("utf-8")


def fetch(params: dict, request_kwargs: dict | None = None) -> Response:
    client = Client(impersonate="chrome_126", verify=False)
    # Pass through any extra request kwargs (e.g., cookies, headers)
    req_kwargs = request_kwargs.copy() if request_kwargs else {}
    res = client.get("https://www.google.com/travel/flights", params=params, **req_kwargs)
    assert res.status_code == 200, f"{res.status_code} Result: {res.text_markdown}"
    return res


def _merge_binary_cookies(cookies_bytes: bytes | None, request_kwargs: dict | None) -> dict:
    """Parse binary cookies into request kwargs.

    Supported formats (in order):
    - JSON bytes -> dict or list of pairs
    - Pickle bytes -> dict
    - Raw cookie header bytes -> sets the 'Cookie' header

    Existing request_kwargs are copied and updated; existing 'cookies' or 'headers' are overridden by parsed values.
    """
    req_kwargs = request_kwargs.copy() if request_kwargs else {}
    if not cookies_bytes:
        return req_kwargs

    # Try JSON first
    try:
        s = cookies_bytes.decode("utf-8")
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            req_kwargs['cookies'] = parsed
            return req_kwargs
        if isinstance(parsed, list):
            # list of pairs
            try:
                req_kwargs['cookies'] = dict(parsed)
                return req_kwargs
            except Exception:
                pass
    except Exception:
        pass

    # Try pickle
    try:
        import pickle

        parsed = pickle.loads(cookies_bytes)
        if isinstance(parsed, dict):
            req_kwargs['cookies'] = parsed
            return req_kwargs
    except Exception:
        pass

    # Fallback: treat as raw Cookie header
    try:
        s = cookies_bytes.decode("utf-8")
        headers = req_kwargs.get('headers', {})
        # make a shallow copy to avoid mutating input
        headers = headers.copy() if isinstance(headers, dict) else {}
        headers['Cookie'] = s
        req_kwargs['headers'] = headers
    except Exception:
        # give up silently and return what we have
        pass

    return req_kwargs


def get_flights_from_filter(
    filter: TFSData,
    currency: str = "",
    *,
    mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "common",
    data_source: DataSource = 'html',
    cookies: bytes | None = None,
    request_kwargs: dict | None = None,
    cookie_consent: bool = True,
) -> Union[Result, DecodedResult, None]:
    data = filter.as_b64()

    params = {
        "tfs": data.decode("utf-8"),
        "hl": "en",
        "tfu": "EgQIABABIgA",
        "curr": currency,
    }

    # If the caller didn't provide cookies bytes and there is no cookies or Cookie header
    # in request_kwargs, use the embedded default cookies bytes (only when enabled).
    if cookies is None and cookie_consent:
        has_cookies_in_req = False
        if request_kwargs:
            if 'cookies' in request_kwargs:
                has_cookies_in_req = True
            elif 'headers' in request_kwargs and isinstance(request_kwargs['headers'], dict) and 'Cookie' in request_kwargs['headers']:
                has_cookies_in_req = True
        if not has_cookies_in_req:
            cookies = _DEFAULT_COOKIES_BYTES

    # Merge binary cookies into request kwargs (binary cookies take precedence)
    req_kwargs = _merge_binary_cookies(cookies, request_kwargs)

    if mode in {"common", "fallback"}:
        try:
            res = fetch(params, request_kwargs=req_kwargs)
        except AssertionError as e:
            if mode == "fallback":
                res = fallback_playwright_fetch(params, request_kwargs=req_kwargs)
            else:
                raise e

    elif mode == "local":
        from .local_playwright import local_playwright_fetch

        res = local_playwright_fetch(params, request_kwargs=req_kwargs)

    elif mode == "bright-data":
        res = bright_data_fetch(params, request_kwargs=req_kwargs)

    else:
        res = fallback_playwright_fetch(params, request_kwargs=req_kwargs)

    try:
        return parse_response(res, data_source)
    except RuntimeError as e:
        if mode == "fallback":
            return get_flights_from_filter(filter, mode="force-fallback", request_kwargs=req_kwargs, cookies=None, cookie_consent=cookie_consent)
        raise e



def get_flights(
    *,
    flight_data: List[FlightData],
    trip: Literal["round-trip", "one-way", "multi-city"],
    passengers: Optional[Passengers] = None,
    # Convenience passenger counters (used when `passengers` is None)
    adults: Optional[int] = None,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat: Literal["economy", "premium-economy", "business", "first"] = "economy",
    fetch_mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "common",
    max_stops: Optional[int] = None,
    data_source: DataSource = 'html',
    cookies: bytes | None = None,
    request_kwargs: dict | None = None,
    cookie_consent: bool = True,
) -> Union[Result, DecodedResult, None]:
    # If the caller didn't supply a Passengers object, build one from the
    # convenience counters. Default to 1 adult when no adults count provided
    # (matches previous typical usage where at least one adult is expected).
    if passengers is None:
        ad = 1 if adults is None else adults
        passengers = Passengers(
            adults=ad,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap,
        )

    tfs: TFSData = TFSData.from_interface(
        flight_data=flight_data,
        trip=trip,
        passengers=passengers,
        seat=seat,
        max_stops=max_stops,
    )

    return get_flights_from_filter(
        tfs,
        mode=fetch_mode,
        data_source=data_source,
        cookies=cookies,
        request_kwargs=request_kwargs,
        cookie_consent=cookie_consent,
    )



def parse_response(
     r: Response,
     data_source: DataSource,
     *,
     dangerously_allow_looping_last_item: bool = False,
 ) -> Union[Result, DecodedResult, None]:
    class _blank:
        def text(self, *_, **__):
            return ""

        def iter(self):
            return []

    blank = _blank()

    def safe(n: Optional[LexborNode]):
        return n or blank

    parser = LexborHTMLParser(r.text)

    if data_source == 'js':
        script = parser.css_first(r'script.ds\:1').text()

        match = re.search(r'^.*?\{.*?data:(\[.*\]).*}', script)
        assert match, 'Malformed js data, cannot find script data'
        data = json.loads(match.group(1))
        return ResultDecoder.decode(data) if data is not None else None

    flights = []

    for i, fl in enumerate(parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')):
        is_best_flight = i == 0

        for item in fl.css("ul.Rk10dc li")[
            : (None if dangerously_allow_looping_last_item or i == 0 else -1)
        ]:
            # Flight name
            name = safe(item.css_first("div.sSHqwe.tPgKwe.ogfYpf span")).text(
                strip=True
            )

            # Attempt to extract flight number from data-travelimpactmodelwebsiteurl attribute
            flight_number = None
            departure_airport = None
            arrival_airport = None
            
            url_elem = item.css_first('[data-travelimpactmodelwebsiteurl]')
            if url_elem:
                url = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
                # Example: ...itinerary=JFK-LAX-F9-2503-20250801
                match = re.search(r'-([A-Z0-9]+)-(\d+)-\d{8}$', url)
                if match:
                    airline_code = match.group(1)
                    flight_number = match.group(2)
                
                # Extract airport codes from the URL
                # Pattern: itinerary=JFK-LAX-F9-2503-20250801
                airport_match = re.search(r'itinerary=([A-Z]{3})-([A-Z]{3})-', url)
                if airport_match:
                    departure_airport = airport_match.group(1)
                    arrival_airport = airport_match.group(2)
            
            # If not found in URL, try to extract from HTML elements
            if not departure_airport or not arrival_airport:
                # Look for airport codes in the route information
                route_elem = item.css_first('.PTuQse')
                if route_elem:
                    route_text = route_elem.text(strip=True)
                    # Pattern: JFK – LAX
                    airport_match = re.search(r'([A-Z]{3})\s*–\s*([A-Z]{3})', route_text)
                    if airport_match:
                        departure_airport = airport_match.group(1)
                        arrival_airport = airport_match.group(2)

            # If still not found, try looking for any span with a pattern like "AA1234", "DL567", etc.
            if not flight_number:
                flight_number_node = item.css_first("div.sSHqwe.tPgKwe.ogfYpf span + span")
                if flight_number_node:
                    candidate = flight_number_node.text(strip=True)
                    # Simple heuristic: must contain both letters and numbers
                    if re.search(r'[A-Z]{2,3}\d{2,4}', candidate):
                        flight_number = candidate

            # Get departure & arrival time
            dp_ar_node = item.css("span.mv1WYe div")
            try:
                departure_time = dp_ar_node[0].text(strip=True)
                arrival_time = dp_ar_node[1].text(strip=True)
            except IndexError:
                # sometimes this is not present
                departure_time = ""
                arrival_time = ""

            # Get arrival time ahead
            time_ahead = safe(item.css_first("span.bOzv6")).text()

            # Get duration
            duration = safe(item.css_first("li div.Ak5kof div")).text()

            # Get flight stops
            stops = safe(item.css_first(".BbR8Ec .ogfYpf")).text()

            # Get delay
            delay = safe(item.css_first(".GsCCve")).text() or None

            # Get prices
            price = safe(item.css_first(".YMlIz.FpEdX")).text() or "0"

            # Stops formatting
            try:
                stops_fmt = 0 if stops == "Nonstop" else int(stops.split(" ", 1)[0])
            except ValueError:
                stops_fmt = "Unknown"

            flights.append(
                {
                    "is_best": is_best_flight,
                    "name": name,
                    "departure": " ".join(departure_time.split()),
                    "arrival": " ".join(arrival_time.split()),
                    "arrival_time_ahead": time_ahead,
                    "duration": duration,
                    "stops": stops_fmt,
                    "delay": delay,
                    "price": price.replace(",", ""),
                    "flight_number": flight_number,
                    "departure_airport": departure_airport,
                    "arrival_airport": arrival_airport,
                }
            )

    current_price = safe(parser.css_first("span.gOatQ")).text()
    if not flights:
        # Extract relevant parts for debugging instead of full HTML
        debug_info = []
        
        # Check if we can find the main flight containers
        flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
        debug_info.append(f"Found {len(flight_containers)} flight containers")
        
        # Check if we can find any flight items
        all_flight_items = parser.css("ul.Rk10dc li")
        debug_info.append(f"Found {len(all_flight_items)} flight items")
        
        # Show first few flight items for debugging
        for i, item in enumerate(all_flight_items[:3]):
            name = safe(item.css_first("div.sSHqwe.tPgKwe.ogfYpf span")).text(strip=True)
            debug_info.append(f"Flight item {i+1}: name='{name}'")
            
            # Show URL element if present
            url_elem = item.css_first('[data-travelimpactmodelwebsiteurl]')
            if url_elem:
                url = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
                debug_info.append(f"  URL: {url[:100]}...")
        
        # Check for script data
        script_elem = parser.css_first(r'script.ds\:1')
        if script_elem:
            debug_info.append("Found script data element")
        else:
            debug_info.append("No script data element found")
        
        debug_output = "\n".join(debug_info)
        raise RuntimeError(f"No flights found. Debug info:\n{debug_output}")

    return Result(current_price=current_price, flights=[Flight(**fl) for fl in flights])  # type: ignore