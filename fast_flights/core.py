import re
import json
from typing import List, Literal, Optional, Union

from selectolax.lexbor import LexborHTMLParser

from .decoder import DecodedResult, ResultDecoder
from .schema import Flight, Result, FlightSegment, Layover
from .flights_impl import FlightData, Passengers
from .filter import TFSData
from .fallback_playwright import fallback_playwright_fetch
from .bright_data_fetch import bright_data_fetch
from .primp import Client, Response




def should_skip_container(container_index: int, container_sizes: List[int]) -> bool:
    """Skip duplicate containers in round-trip search results.
    
    In round-trip results, Google Flights shows the same flights twice:
    - Containers 0 & 2: "best" flights (duplicates)
    - Containers 1 & 3: "other" flights (duplicates)
    
    We only need to process containers 0 & 1 to avoid duplicates.
    """
    # Common pattern for round-trip: [3, 106, 3, 106] or similar
    if len(container_sizes) == 4:
        # Check if it's a duplicate pattern (containers 0&2 and 1&3 have same sizes)
        if container_sizes[0] == container_sizes[2] and container_sizes[1] == container_sizes[3]:
            return container_index >= 2
    return False


def extract_enrichments_from_container(parser: LexborHTMLParser, container_jsname: str) -> List[dict]:
    """Extract enrichments from a specific container type."""
    enrichments = []
    
    # Get all containers of the specified type
    containers = parser.css(f'div[jsname="{container_jsname}"]')
    
    for container in containers:
        # Get flight items within this container
        flight_items = container.css("ul.Rk10dc li")
        
        # For "other" flights container, exclude last item to match HTML parser behavior
        if container_jsname == "YdtKid":
            flight_items = flight_items[:-1]
        
        for item in flight_items:
            enrichment = {}
            
            # Extract emissions data - look for emissions elements within this flight item
            emissions_elems = item.css('[aria-label*="emissions"], [aria-label*="CO2"], [aria-label*="carbon"]')
            for emissions_elem in emissions_elems:
                aria_label = emissions_elem.attributes.get('aria-label', '')
                if 'emissions estimate' in aria_label.lower():
                    # Pattern: "Carbon emissions estimate: 502 kilograms. -22% emissions."
                    kg_match = re.search(r'(\d+)\s*kilogram', aria_label)
                    percent_match = re.search(r'([+-]?\d+)%\s*emissions', aria_label)
                    if kg_match or percent_match:
                        enrichment['emissions'] = {}
                        if kg_match:
                            enrichment['emissions']['kg'] = int(kg_match.group(1))
                        if percent_match:
                            enrichment['emissions']['percentage'] = int(percent_match.group(1))
                        break  # Found emissions for this flight
            
            # Extract operated by info from aria-label
            # Check the main flight item aria-label and also any sub-elements with aria-labels
            aria_label = item.attributes.get('aria-label', '')
            
            # Also check the main container div (like JMc5Xc) within the item
            main_container = item.css_first('.JMc5Xc')
            if main_container:
                container_aria_label = main_container.attributes.get('aria-label', '')
                if container_aria_label:
                    aria_label = container_aria_label
            
            if aria_label:
                operated_pattern = r'Operated by ([^.,]+)'
                operated_matches = re.findall(operated_pattern, aria_label)
                if operated_matches:
                    enrichment['operated_by'] = list(set(operated_matches))
            
            # Extract detailed aircraft info (this would need more specific selectors)
            # For now, look in the aria-label for aircraft mentions
            if aria_label:
                aircraft_pattern = r'(Boeing|Airbus|Embraer|Bombardier)\s+([A-Z0-9-]+)'
                aircraft_matches = re.findall(aircraft_pattern, aria_label)
                if aircraft_matches:
                    enrichment['aircraft_details'] = f"{aircraft_matches[0][0]} {aircraft_matches[0][1]}"
                
            
            # Extract arrival time ahead using the CSS selector that works
            time_ahead_elem = item.css_first("span.bOzv6")
            if time_ahead_elem:
                time_ahead_text = time_ahead_elem.text(strip=True)
                if time_ahead_text:
                    enrichment['arrival_time_ahead'] = time_ahead_text
            
            # Also try to extract from aria-label as fallback
            if aria_label and 'arrival_time_ahead' not in enrichment:
                # Look for time zone indicators in aria-label
                time_ahead_pattern = r'(\+\d+)\s*day|(\+\d+)\s*hr'
                time_ahead_match = re.search(time_ahead_pattern, aria_label)
                if time_ahead_match:
                    time_ahead = time_ahead_match.group(1) or time_ahead_match.group(2)
                    enrichment['arrival_time_ahead'] = time_ahead
            
            # Extract delay information
            # First try CSS selector (though it doesn't exist in Bright Data HTML)
            delay_elem = item.css_first(".GsCCve")
            if delay_elem:
                delay_text = delay_elem.text(strip=True)
                if delay_text:
                    enrichment['delay'] = delay_text
            
            # Also check aria-label for delay information as fallback
            if aria_label and 'delay' not in enrichment:
                delay_pattern = r'delayed|late|(\d+)\s*min\s*delay'
                delay_match = re.search(delay_pattern, aria_label, re.IGNORECASE)
                if delay_match:
                    delay_text = delay_match.group(0) if delay_match.group(0) else f"{delay_match.group(1)} min delay"
                    enrichment['delay'] = delay_text
            
            # Extract flight URL for matching
            url_elem = item.css_first('[data-travelimpactmodelwebsiteurl]')
            if url_elem:
                enrichment['url'] = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
            
            enrichments.append(enrichment)
    
    return enrichments


def extract_html_enrichments(parser: LexborHTMLParser, html_content: str) -> List[dict]:
    """Extract additional flight data from HTML that's not available in JS."""
    enrichments = []
    
    # Use the same structure as the HTML parser - first get flight containers, then items within
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    
    # Get container sizes to detect duplicate pattern
    container_sizes = [len(container.css("ul.Rk10dc li")) for container in flight_containers]
    
    for container_idx, container in enumerate(flight_containers):
        # Skip duplicate containers in round-trip results
        if should_skip_container(container_idx, container_sizes):
            continue
            
        # Get flight items within this container
        flight_items = container.css("ul.Rk10dc li")
        
        # Match the HTML parser behavior: exclude last item for non-first containers
        # This ensures enrichment count matches flight count
        items_to_process = flight_items if container_idx == 0 else flight_items[:-1]
        
        for item in items_to_process:
            enrichment = {}
            
            # Extract emissions data - look for emissions elements within this flight item
            emissions_elems = item.css('[aria-label*="emissions"], [aria-label*="CO2"], [aria-label*="carbon"]')
            for emissions_elem in emissions_elems:
                aria_label = emissions_elem.attributes.get('aria-label', '')
                if 'emissions estimate' in aria_label.lower():
                    # Pattern: "Carbon emissions estimate: 502 kilograms. -22% emissions."
                    kg_match = re.search(r'(\d+)\s*kilogram', aria_label)
                    percent_match = re.search(r'([+-]?\d+)%\s*emissions', aria_label)
                    if kg_match or percent_match:
                        enrichment['emissions'] = {}
                        if kg_match:
                            enrichment['emissions']['kg'] = int(kg_match.group(1))
                        if percent_match:
                            enrichment['emissions']['percentage'] = int(percent_match.group(1))
                        break  # Found emissions for this flight
            
            # Extract operated by info from aria-label
            # Check the main flight item aria-label and also any sub-elements with aria-labels
            aria_label = item.attributes.get('aria-label', '')
            
            # Also check the main container div (like JMc5Xc) within the item
            main_container = item.css_first('.JMc5Xc')
            if main_container:
                container_aria_label = main_container.attributes.get('aria-label', '')
                if container_aria_label:
                    aria_label = container_aria_label
            
            if aria_label:
                operated_pattern = r'Operated by ([^.,]+)'
                operated_matches = re.findall(operated_pattern, aria_label)
                if operated_matches:
                    enrichment['operated_by'] = list(set(operated_matches))
            
            # Extract detailed aircraft info (this would need more specific selectors)
            # For now, look in the aria-label for aircraft mentions
            if aria_label:
                aircraft_pattern = r'(Boeing|Airbus|Embraer|Bombardier)\s+([A-Z0-9-]+)'
                aircraft_matches = re.findall(aircraft_pattern, aria_label)
                if aircraft_matches:
                    enrichment['aircraft_details'] = f"{aircraft_matches[0][0]} {aircraft_matches[0][1]}"
                
            
            # Extract arrival time ahead using the CSS selector that works
            time_ahead_elem = item.css_first("span.bOzv6")
            if time_ahead_elem:
                time_ahead_text = time_ahead_elem.text(strip=True)
                if time_ahead_text:
                    enrichment['arrival_time_ahead'] = time_ahead_text
            
            # Also try to extract from aria-label as fallback
            if aria_label and 'arrival_time_ahead' not in enrichment:
                # Look for time zone indicators in aria-label
                time_ahead_pattern = r'(\+\d+)\s*day|(\+\d+)\s*hr'
                time_ahead_match = re.search(time_ahead_pattern, aria_label)
                if time_ahead_match:
                    time_ahead = time_ahead_match.group(1) or time_ahead_match.group(2)
                    enrichment['arrival_time_ahead'] = time_ahead
            
            # Extract delay information
            # First try CSS selector (though it doesn't exist in Bright Data HTML)
            delay_elem = item.css_first(".GsCCve")
            if delay_elem:
                delay_text = delay_elem.text(strip=True)
                if delay_text:
                    enrichment['delay'] = delay_text
            
            # Also check aria-label for delay information as fallback
            if aria_label and 'delay' not in enrichment:
                delay_pattern = r'delayed|late|(\d+)\s*min\s*delay'
                delay_match = re.search(delay_pattern, aria_label, re.IGNORECASE)
                if delay_match:
                    delay_text = delay_match.group(0) if delay_match.group(0) else f"{delay_match.group(1)} min delay"
                    enrichment['delay'] = delay_text
            
            # Extract flight URL for matching
            url_elem = item.css_first('[data-travelimpactmodelwebsiteurl]')
            if url_elem:
                enrichment['url'] = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
            
            enrichments.append(enrichment)
    
    return enrichments


def combine_results_structural(js_result: Result, parser: LexborHTMLParser) -> Result:
    """Combine JS parsing results with HTML enrichments using structural matching."""
    # Separate JS flights by is_best flag
    js_best = [f for f in js_result.flights if f.is_best]
    js_other = [f for f in js_result.flights if not f.is_best]
    
    # Extract enrichments by container type
    # IWWDBc = best flights, YdtKid = other flights
    best_enrichments = extract_enrichments_from_container(parser, 'IWWDBc')
    other_enrichments = extract_enrichments_from_container(parser, 'YdtKid')
    
    # Helper function to match within a category
    def apply_enrichments_to_category(flights: List[Flight], enrichments: List[dict]):
        """Apply enrichments to flights within a category (best or other)."""
        # Create URL mapping for enrichments
        enrichment_by_url = {}
        for idx, enrichment in enumerate(enrichments):
            if 'url' in enrichment and enrichment['url']:
                enrichment_by_url[enrichment['url']] = (idx, enrichment)
        
        # Track used enrichments
        used_indices = set()
        
        for flight in flights:
            enrichment = None
            
            # Try URL-based matching first
            if flight.flight_number and flight.departure_airport and flight.arrival_airport:
                flight_num_for_url = flight.flight_number.replace(' ', '-')
                
                best_match_idx = None
                best_match_enrichment = None
                
                for url, (idx, enrich) in enrichment_by_url.items():
                    if idx in used_indices:
                        continue
                    
                    # For connecting flights, JS only shows first segment's flight number
                    if flight_num_for_url in url and f"{flight.departure_airport}-" in url:
                        # Prefer exact match for direct flights
                        if f"{flight.departure_airport}-{flight.arrival_airport}-{flight_num_for_url}" in url:
                            best_match_idx = idx
                            best_match_enrichment = enrich
                            break  # Exact match found
                        # Otherwise accept if departure airport and flight number match
                        elif best_match_idx is None:
                            best_match_idx = idx
                            best_match_enrichment = enrich
                
                if best_match_enrichment:
                    enrichment = best_match_enrichment
                    used_indices.add(best_match_idx)
            
            # Apply enrichment if found
            if enrichment:
                if 'emissions' in enrichment:
                    flight.emissions = enrichment['emissions']
                if 'operated_by' in enrichment:
                    flight.operated_by = enrichment['operated_by']
                if 'aircraft_details' in enrichment:
                    flight.aircraft_details = enrichment['aircraft_details']
                if 'arrival_time_ahead' in enrichment:
                    flight.arrival_time_ahead = enrichment['arrival_time_ahead']
                if 'delay' in enrichment:
                    flight.delay = enrichment['delay']
    
    # Apply enrichments to each category
    apply_enrichments_to_category(js_best, best_enrichments)
    apply_enrichments_to_category(js_other, other_enrichments)
    
    # Also check if connections have aircraft data and create aircraft_details if not set
    for flight in js_result.flights:
        if flight.connections and not flight.aircraft_details:
            # Check if any segment has unique aircraft
            aircraft_types = []
            for conn in flight.connections:
                # Only check aircraft for FlightSegment objects, not Layovers
                if hasattr(conn, 'aircraft') and conn.aircraft and conn.aircraft not in aircraft_types:
                    aircraft_types.append(conn.aircraft)
            
            if aircraft_types:
                # If all segments use same aircraft, set it as flight aircraft
                if len(aircraft_types) == 1:
                    flight.aircraft_details = aircraft_types[0]
                # Otherwise list all unique aircraft
                elif len(aircraft_types) > 1:
                    flight.aircraft_details = " / ".join(aircraft_types)
    
    return js_result



def convert_decoded_to_result(decoded: DecodedResult) -> Result:
    """Convert a DecodedResult from JS parser to a Result with connections."""
    flights = []
    
    # Process all itineraries (best and other)
    all_itineraries = decoded.best + decoded.other
    
    for idx, itinerary in enumerate(all_itineraries):
        is_best = idx < len(decoded.best)
        
        # Create connections list from individual flights
        connections = []
        
        # First, collect airport codes from layovers for reference
        layover_airports = []
        if itinerary.layovers:
            for layover in itinerary.layovers:
                layover_airports.append(layover.departure_airport)
                if hasattr(layover, 'arrival_airport') and layover.arrival_airport:
                    layover_airports.append(layover.arrival_airport)
        
        for i, flight in enumerate(itinerary.flights):
            # Handle departure/arrival times that might be in different formats
            def format_time(time_data):
                """Format time data into HH:MM string"""
                try:
                    if isinstance(time_data, (list, tuple)):
                        if len(time_data) >= 2:
                            return f"{time_data[0]}:{time_data[1]:02d}"
                        elif len(time_data) == 1:
                            return f"{time_data[0]}:00"
                        else:
                            return ""
                    elif isinstance(time_data, int):
                        return f"{time_data}:00"
                    elif time_data is None:
                        return ""
                    else:
                        return str(time_data)
                except (TypeError, ValueError, IndexError):
                    return str(time_data) if time_data is not None else ""
            
            departure_str = format_time(flight.departure_time)
            arrival_str = format_time(flight.arrival_time)
            
            # Fix airport codes that might be full names instead
            departure_airport = flight.departure_airport
            arrival_airport = flight.arrival_airport
            
            # If the airport field contains a name (>4 chars), try to fix it
            if departure_airport and len(departure_airport) > 4:
                # This is an airport name, not a code
                # For first flight, use itinerary departure airport
                if i == 0:
                    departure_airport = itinerary.departure_airport
                # For connecting flights, use the layover airport code
                elif i - 1 < len(layover_airports):
                    departure_airport = layover_airports[i - 1]
            
            if arrival_airport and len(arrival_airport) > 4:
                # This is an airport name, not a code
                # For last flight, use itinerary arrival airport
                if i == len(itinerary.flights) - 1:
                    arrival_airport = itinerary.arrival_airport
                # For connecting flights, use the layover airport code
                elif i < len(layover_airports):
                    arrival_airport = layover_airports[i]
            
            connection = FlightSegment(
                departure=departure_str,
                arrival=arrival_str,
                arrival_time_ahead="",  # Not available in decoded data
                duration=f"{flight.travel_time // 60} hr {flight.travel_time % 60} min" if flight.travel_time >= 60 else f"{flight.travel_time} min",
                name=flight.airline_name,
                delay=None,  # Not available in decoded data
                flight_number=f"{flight.airline} {flight.flight_number}",
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                aircraft=flight.aircraft if hasattr(flight, 'aircraft') and flight.aircraft else None
            )
            connections.append(connection)
            
            # Add layover after each flight segment except the last one
            if i < len(itinerary.flights) - 1 and itinerary.layovers and i < len(itinerary.layovers):
                layover = itinerary.layovers[i]
                duration_str = f"{layover.minutes // 60} hr {layover.minutes % 60} min" if layover.minutes >= 60 else f"{layover.minutes} min"
                connections.append(Layover(duration=duration_str))
        
        
        # Format times using the same helper function
        def format_time(time_data):
            """Format time data into HH:MM string"""
            try:
                if isinstance(time_data, (list, tuple)):
                    if len(time_data) >= 2:
                        return f"{time_data[0]}:{time_data[1]:02d}"
                    elif len(time_data) == 1:
                        return f"{time_data[0]}:00"
                    else:
                        return ""
                elif isinstance(time_data, int):
                    return f"{time_data}:00"
                elif time_data is None:
                    return ""
                else:
                    return str(time_data)
            except (TypeError, ValueError, IndexError):
                return str(time_data) if time_data is not None else ""
        
        departure_time = format_time(itinerary.departure_time)
        arrival_time = format_time(itinerary.arrival_time)
        
        # Format duration
        total_minutes = itinerary.travel_time
        duration = f"{total_minutes // 60} hr {total_minutes % 60} min" if total_minutes >= 60 else f"{total_minutes} min"
        
        # Get price from itinerary summary (already in dollars)
        try:
            price = float(itinerary.itinerary_summary.price) if itinerary.itinerary_summary.price else 0.0
        except (TypeError, ValueError, AttributeError):
            price = 0.0
        
        # Build flight object
        flight = Flight(
            is_best=is_best,
            name=" + ".join(itinerary.airline_names) if itinerary.airline_names else "",
            departure=departure_time,
            arrival=arrival_time,
            arrival_time_ahead="",  # Not available in decoded data
            duration=duration,
            stops=len(itinerary.flights) - 1,  # Number of stops is number of flights - 1
            delay=None,  # Not available in decoded data
            price=price,
            flight_number=connections[0].flight_number if connections else (itinerary.itinerary_summary.flights[0] if itinerary.itinerary_summary.flights else None),
            departure_airport=itinerary.departure_airport,
            arrival_airport=itinerary.arrival_airport,
            connections=connections if len(connections) > 1 else None  # Only include if multi-segment
        )
        
        # For direct flights (no connections), set aircraft_details from the single segment
        if flight.stops == 0 and itinerary.flights and itinerary.flights[0].aircraft:
            flight.aircraft_details = itinerary.flights[0].aircraft
        
        flights.append(flight)
    
    # Determine current price level (not available in decoded data, default to "typical")
    current_price = "typical"
    
    return Result(current_price=current_price, flights=flights)


def fetch(params: dict) -> Response:
    client = Client(impersonate="chrome_126", verify=False)
    res = client.get("https://www.google.com/travel/flights", params=params)
    assert res.status_code == 200, f"{res.status_code} Result: {res.text_markdown}"
    return res

def get_flights_from_filter(
    filter: TFSData,
    currency: str = "",
    *,
    mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "common",
) -> Result:
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
        return parse_response(res)
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
) -> Result:
    return get_flights_from_filter(
        TFSData.from_interface(
            flight_data=flight_data,
            trip=trip,
            passengers=passengers,
            seat=seat,
            max_stops=max_stops,
        ),
        mode=fetch_mode,
    )


def parse_response(r: Response) -> Result:
    parser = LexborHTMLParser(r.text)

    # First get JS data for segment details
    script = parser.css_first(r'script.ds\:1').text()
    match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script)
    assert match, 'Malformed js data, cannot find script data'
    data = json.loads(match.group(1))
    decoded = ResultDecoder.decode(data) if data is not None else None
    if decoded is None:
        raise RuntimeError("No flights found in JS data")
    js_result = convert_decoded_to_result(decoded)
    
    # Use structural matching instead of index-based
    return combine_results_structural(js_result, parser)
