import json

from selectolax.lexbor import LexborHTMLParser

from .model import (
    Airline,
    Airport,
    Alliance,
    CarbonEmission,
    Flights,
    JsMetadata,
    SimpleDatetime,
    SingleFlight,
)


class MetaList(list[Flights]):
    """Searched flights list, with metadata attached."""

    metadata: JsMetadata


import re

def parse(html: str) -> MetaList:
    # Try multiple ways to find the data
    
    # 1. Classic script tag with ID or class
    parser = LexborHTMLParser(html)
    for selector in [r"script.ds\:1", r"script#ds\:1", r"script[data-id='ds:1']"]:
        script = parser.css_first(selector)
        if script and "data:" in script.text():
            try:
                return parse_js(script.text())
            except:
                continue

    # 2. AF_initDataCallback style
    match = re.search(r"AF_initDataCallback\(\{key:\s*'ds:1'.*?data:(.*?)\}\);</script>", html, re.DOTALL)
    if not match:
        # Try without the script tag end
        match = re.search(r"AF_initDataCallback\(\{key:\s*'ds:1'.*?data:(.*?)\}\);", html, re.DOTALL)
        
    if match:
        data = match.group(1).strip()
        return parse_payload(data)

    # 3. WIZ style (wiz_jd)
    match = re.search(r"window\['_wjdc'\]\(.*?'ds:1':\s*JSON\.parse\('(.*?)'\)", html, re.DOTALL)
    if match:
        data = match.group(1).encode().decode('unicode_escape')
        return parse_payload(data)

    # Check for consent page or other common issues
    if "consent.google.com" in html or "Before you continue" in html:
        raise RuntimeError("Google Consent Page detected. Scraper blocked.")
    
    raise RuntimeError("Could not find flight data in Google Flights response.")

def parse_js(js: str):
    data = js.split("data:", 1)[1].rsplit(",", 1)[0]
    return parse_payload(data)

def parse_payload(data: str):
    data = data.strip()
    if data.startswith("'") or data.startswith('"'):
        # It's a string, likely from WIZ style
        try:
            data = json.loads(data)
        except:
            # Maybe it's just quoted but not a JSON string
            if data[0] == data[-1] and data[0] in ("'", '"'):
                data = data[1:-1]
    
    # If it's still a string, it might have trailing junk like ", sideChannel: {}"
    # We expect a JSON array or object
    if data.startswith('['):
        last_bracket = data.rfind(']')
        if last_bracket != -1:
            data = data[:last_bracket+1]
    elif data.startswith('{'):
        last_bracket = data.rfind('}')
        if last_bracket != -1:
            data = data[:last_bracket+1]

    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        # One last attempt: maybe it's a JS-style object that needs some cleaning
        # but usually Google's data is strict JSON inside the callback
        raise

    alliances = []
    airlines = []

    try:
        (alliances_data, airlines_data) = (
            payload[7][1][0],
            payload[7][1][1],
        )

        for code, name in alliances_data:
            alliances.append(Alliance(code=code, name=name))

        for code, name in airlines_data:
            airlines.append(Airline(code=code, name=name))
    except (IndexError, TypeError):
        # Metadata missing or different format, skip it
        pass

    meta = JsMetadata(alliances=alliances, airlines=airlines)

    flights = MetaList()
    if len(payload) <= 3 or payload[3] is None or payload[3][0] is None:
        return flights

    for k in payload[3][0]:
        flight = k[0]
        price = k[1][0][1]

        typ = flight[0]
        airlines = flight[1]

        sg_flights = []

        # multiple flights!
        for single_flight in flight[2]:
            from_airport = Airport(code=single_flight[3], name=single_flight[4])
            to_airport = Airport(code=single_flight[6], name=single_flight[5])
            departure_time = single_flight[8]
            departure_date = single_flight[20]
            departure = SimpleDatetime(date=departure_date, time=departure_time)

            arrival_time = single_flight[10]
            arrival_date = single_flight[21]
            arrival = SimpleDatetime(date=arrival_date, time=arrival_time)

            plane_type = single_flight[17]

            duration = single_flight[11]

            sg_flights.append(
                SingleFlight(
                    from_airport=from_airport,
                    to_airport=to_airport,
                    departure=departure,
                    arrival=arrival,
                    duration=duration,
                    plane_type=plane_type,
                )
            )

        # some additional data
        extras = flight[22]
        carbon_emission = extras[7]
        typical_carbon_emission = extras[8]

        flights.append(
            Flights(
                type=typ,
                price=price,
                airlines=airlines,
                flights=sg_flights,
                carbon=CarbonEmission(
                    typical_on_route=typical_carbon_emission, emission=carbon_emission
                ),
            )
        )

    flights.metadata = meta
    return flights
