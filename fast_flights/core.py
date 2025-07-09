import re
import json
from typing import List, Literal, Optional, Union, overload

from selectolax.lexbor import LexborHTMLParser, LexborNode

from .decoder import DecodedResult, ResultDecoder
from .schema import Flight, Result
from .flights_impl import FlightData, Passengers
from .filter import TFSData
from .fallback_playwright import fallback_playwright_fetch
from .bright_data_fetch import bright_data_fetch
from .primp import Client, Response


DataSource = Literal['html', 'js']

def fetch(params: dict) -> Response:
    client = Client(impersonate="chrome_126", verify=False)
    res = client.get("https://www.google.com/travel/flights", params=params)
    assert res.status_code == 200, f"{res.status_code} Result: {res.text_markdown}"
    return res

@overload
def get_flights_from_filter(
    filter: TFSData,
    currency: str = "",
    *,
    mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "common",
    data_source: Literal['js'] = ...,
) -> Union[DecodedResult, None]: ...

@overload
def get_flights_from_filter(
    filter: TFSData,
    currency: str = "",
    *,
    mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "common",
    data_source: Literal['html'],
) -> Result: ...

def get_flights_from_filter(
    filter: TFSData,
    currency: str = "",
    *,
    mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "common",
    data_source: DataSource = 'html',
) -> Union[Result, DecodedResult, None]:
    data = filter.as_b64()

    params = {
        "tfs": data.decode("utf-8"),
        "hl": "en",
        "tfu": "EgQIABABIgA",
        "curr": currency,
    }

    if mode in {"common", "fallback"}:
        try:
            res = fetch(params)
        except AssertionError as e:
            if mode == "fallback":
                res = fallback_playwright_fetch(params)
            else:
                raise e

    elif mode == "local":
        from .local_playwright import local_playwright_fetch

        res = local_playwright_fetch(params)

    elif mode == "bright-data":
        res = bright_data_fetch(params)

    else:
        res = fallback_playwright_fetch(params)

    try:
        return parse_response(res, data_source)
    except RuntimeError as e:
        if mode == "fallback":
            return get_flights_from_filter(filter, mode="force-fallback")
        raise e


def get_flights(
    *,
    flight_data: List[FlightData],
    trip: Literal["round-trip", "one-way", "multi-city"],
    passengers: Passengers,
    seat: Literal["economy", "premium-economy", "business", "first"],
    fetch_mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "common",
    max_stops: Optional[int] = None,
    data_source: DataSource = 'html',
) -> Union[Result, DecodedResult, None]:
    return get_flights_from_filter(
        TFSData.from_interface(
            flight_data=flight_data,
            trip=trip,
            passengers=passengers,
            seat=seat,
            max_stops=max_stops,
        ),
        mode=fetch_mode,
        data_source=data_source,
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

        match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script)
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
            connecting_airports = []
            
            url_elem = item.css_first('[data-travelimpactmodelwebsiteurl]')
            if url_elem:
                url = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
                # Example: ...itinerary=JFK-LAX-F9-2503-20250801
                match = re.search(r'-([A-Z0-9]+)-(\d+)-\d{8}$', url)
                if match:
                    airline_code = match.group(1)
                    flight_number = f"{airline_code} {match.group(2)}"
                
                # Extract full route from the URL
                # Pattern: itinerary=JFK-LAX-F9-2503-20250801 (direct)
                # Pattern: itinerary=JFK-MCO-F9-4871-20250801,MCO-LAX-F9-4145-20250801 (with connection)
                route_match = re.search(r'itinerary=([A-Z0-9,-]+)-[A-Z0-9]+-\d+-\d{8}', url)
                if route_match:
                    itinerary = route_match.group(1)
                    # Split on commas to handle connecting flights
                    segments = itinerary.split(',')
                    
                    if len(segments) == 1:
                        # Direct flight
                        route_parts = segments[0].split('-')
                        if len(route_parts) >= 2:
                            departure_airport = route_parts[0]
                            arrival_airport = route_parts[-1]
                            connecting_airports = None
                    else:
                        # Connecting flight
                        first_segment = segments[0].split('-')
                        last_segment = segments[-1].split('-')
                        
                        if len(first_segment) >= 2 and len(last_segment) >= 2:
                            departure_airport = first_segment[0]
                            arrival_airport = last_segment[-1]
                            
                            # Extract connecting airports
                            connecting_airports = []
                            if len(segments) == 2:
                                # 2-segment flight: extract connecting airport from second segment
                                connecting_airports.append(last_segment[0])  # First airport of second segment
                            else:
                                # Multi-segment flight: extract from intermediate segments
                                for segment in segments[1:-1]:  # Skip first and last segments
                                    segment_parts = segment.split('-')
                                    if len(segment_parts) >= 2:
                                        connecting_airports.append(segment_parts[0])  # First airport in each intermediate segment
                            
                            connecting_airports = connecting_airports if connecting_airports else None
                # Do not overwrite arrival_airport or connecting_airports with HTML-derived values

            # If not found in URL, try to extract from HTML elements
            if not departure_airport or not arrival_airport:
                # Look for airport codes in the HTML elements
                departure_elem = item.css_first('div.G2WY5c div')
                arrival_elem = item.css_first('div.c8rWCd div')
                
                if departure_elem and not departure_airport:
                    departure_airport = departure_elem.text(strip=True)
                if arrival_elem and not arrival_airport:
                    arrival_airport = arrival_elem.text(strip=True)

            # If still not found, try looking for any span with a pattern like "AA1234", "DL567", etc.
            if not flight_number:
                flight_number_node = item.css_first("div.sSHqwe.tPgKwe.ogfYpf span + span")
                if flight_number_node:
                    candidate = flight_number_node.text(strip=True)
                    # Simple heuristic: must contain both letters and numbers
                    match = re.search(r'([A-Z]{2,3})(\d{2,4})', candidate)
                    if match:
                        flight_number = f"{match.group(1)} {match.group(2)}"

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
                    "connecting_airports": connecting_airports if connecting_airports else None,
                }
            )

    current_price = safe(parser.css_first("span.gOatQ")).text()
    if not flights:
        raise RuntimeError("No flights found:\n{}".format(r.text_markdown))

    return Result(current_price=current_price, flights=[Flight(**fl) for fl in flights])  # type: ignore
