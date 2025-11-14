"""Generate TFS URL for return flight selection after choosing outbound flight."""

import base64
import re
from dataclasses import dataclass
from typing import Optional, List, Literal, Dict, Any
from . import flights_pb2 as PB


def create_return_flight_filter(
    *,
    outbound_date: str,
    outbound_from: str,
    outbound_to: str,
    outbound_airline: str,
    outbound_flight_number: str,
    return_date: str,
    location_id: str = "/m/0d6lp",  # Default Google entity ID
    connecting_segments: Optional[List[Dict[str, str]]] = None,  # For multi-leg flights
) -> str:
    """Create a TFS filter for viewing return flights after selecting an outbound flight.

    This generates the second-stage TFS URL that shows return flight options
    after a user has selected a specific outbound flight (direct or connecting).

    Args:
        outbound_date (str): Outbound flight date (YYYY-MM-DD format).
        outbound_from (str): Departure airport code for first segment (e.g., "SFO").
        outbound_to (str): Arrival airport code for final segment (e.g., "MCO").
        outbound_airline (str): Airline code for first segment (e.g., "UA").
        outbound_flight_number (str): Flight number for first segment (e.g., "2018").
        return_date (str): Return flight date (YYYY-MM-DD format).
        location_id (str, optional): Google location entity ID. Defaults to "/m/0d6lp".
        connecting_segments (list, optional): Additional flight segments for connecting flights.
            Each segment should be a dict with keys: 'from', 'to', 'airline', 'flight_number'.
            Example for SFO→LAS→MCO: [{'from': 'LAS', 'to': 'MCO', 'airline': 'F9', 'flight_number': '1876'}]

    Returns:
        str: Base64-encoded TFS parameter for the return flight query URL.

    Examples:
        Direct flight:
        >>> tfs = create_return_flight_filter(
        ...     outbound_date="2025-11-18",
        ...     outbound_from="SFO",
        ...     outbound_to="MCO",
        ...     outbound_airline="UA",
        ...     outbound_flight_number="2018",
        ...     return_date="2025-11-25"
        ... )

        Connecting flight (SFO→LAS→MCO):
        >>> tfs = create_return_flight_filter(
        ...     outbound_date="2025-11-18",
        ...     outbound_from="SFO",
        ...     outbound_to="MCO",
        ...     outbound_airline="F9",
        ...     outbound_flight_number="4158",
        ...     connecting_segments=[
        ...         {'from': 'LAS', 'to': 'MCO', 'airline': 'F9', 'flight_number': '1876'}
        ...     ],
        ...     return_date="2025-11-25"
        ... )
    """
    query = PB.ReturnFlightQuery()

    # Set root fields
    query.query_type = 28
    query.step = 2
    query.field_8 = 1
    query.field_9 = 1
    query.field_14 = 1
    query.field_19 = 1

    # Set field_16 (contains -1 as sint64)
    query.field_16.value = -1

    # First leg: Outbound flight with selection
    outbound_leg = query.legs.add()
    outbound_leg.date = outbound_date

    # Add first flight segment
    first_segment = outbound_leg.selected_flight.add()
    first_segment.from_airport = outbound_from
    first_segment.date = outbound_date
    first_segment.to_airport = connecting_segments[0]['from'] if connecting_segments else outbound_to
    first_segment.airline = outbound_airline
    first_segment.flight_number = outbound_flight_number

    # Add additional segments for connecting flights
    if connecting_segments:
        for segment in connecting_segments:
            additional_segment = outbound_leg.selected_flight.add()
            additional_segment.from_airport = segment['from']
            additional_segment.date = outbound_date
            additional_segment.to_airport = segment['to']
            additional_segment.airline = segment['airline']
            additional_segment.flight_number = segment['flight_number']

        # Set max_stops for connecting flights
        outbound_leg.max_stops = len(connecting_segments)

    # Location filters for outbound leg
    outbound_leg.location_filter_1.filter_type = 2
    outbound_leg.location_filter_1.value = location_id

    outbound_leg.location_filter_2.filter_type = 1
    outbound_leg.location_filter_2.value = outbound_to

    # Second leg: Return flight (no selection yet)
    return_leg = query.legs.add()
    return_leg.date = return_date

    # Set max_stops for return leg (match outbound if connecting flight)
    if connecting_segments:
        return_leg.max_stops = len(connecting_segments)

    # Location filters for return leg
    return_leg.location_filter_1.filter_type = 1
    return_leg.location_filter_1.value = outbound_to

    return_leg.location_filter_2.filter_type = 2
    return_leg.location_filter_2.value = location_id

    # Serialize and encode
    serialized = query.SerializeToString()
    encoded = base64.b64encode(serialized).decode('utf-8')

    return encoded


def create_return_flight_url(
    *,
    outbound_date: str,
    outbound_from: str,
    outbound_to: str,
    outbound_airline: str,
    outbound_flight_number: str,
    return_date: str,
    location_id: str = "/m/0d6lp",
) -> str:
    """Create a TFS string for viewing return flights.

    This is an alias for create_return_flight_filter for backwards compatibility.

    Args:
        Same as create_return_flight_filter.

    Returns:
        str: Base64-encoded TFS parameter for the return flight query.

    Example:
        >>> tfs = create_return_flight_url(
        ...     outbound_date="2025-11-18",
        ...     outbound_from="SFO",
        ...     outbound_to="MCO",
        ...     outbound_airline="UA",
        ...     outbound_flight_number="2018",
        ...     return_date="2025-11-25"
        ... )
        >>> # Use with get_flights_from_tfs
        >>> from fast_flights import get_flights_from_tfs
        >>> flights = get_flights_from_tfs(tfs, mode='local')
        >>> # Or construct URL manually
        >>> url = f"https://www.google.com/travel/flights?tfs={tfs}"
    """
    return create_return_flight_filter(
        outbound_date=outbound_date,
        outbound_from=outbound_from,
        outbound_to=outbound_to,
        outbound_airline=outbound_airline,
        outbound_flight_number=outbound_flight_number,
        return_date=return_date,
        location_id=location_id,
    )


@dataclass
class ReturnFlightOption:
    """Details for a single return flight option.

    Represents a specific return flight choice with decoded flight number
    and all available flight details.
    """
    # Return flight identification (decoded from TFS)
    airline: str
    flight_number: str

    # Flight details
    departure_airport: str
    arrival_airport: str
    departure_date: str
    departure_time: str  # e.g., "06:30"
    arrival_time: str    # e.g., "09:38"
    duration_minutes: int
    stops: int

    # Pricing
    total_price: float
    currency: str

    # Additional details
    aircraft: Optional[str] = None

    # TFS for this specific selection (both outbound + this return)
    tfs: str = ""

    # Raw itinerary data (optional, for advanced use)
    raw_itinerary: Optional[Any] = None


def decode_return_flight_tfs(tfs: str) -> Dict[str, Any]:
    """Decode a return flight TFS to extract selected flight details.

    Args:
        tfs: Base64-encoded TFS string representing a complete round-trip selection

    Returns:
        dict: Dictionary with 'outbound' and 'return' flight details

    Raises:
        ValueError: If TFS is invalid or doesn't contain both flight selections

    Example:
        >>> tfs = "CBwQAhpFEgoyMDI1LTExLTE4..."
        >>> details = decode_return_flight_tfs(tfs)
        >>> print(details['return']['flight_number'])  # e.g., "626"
    """
    try:
        # Add padding if needed for base64 decoding
        tfs_padded = tfs + "=" * ((4 - len(tfs) % 4) % 4)

        # Try URL-safe decoding first, fall back to standard
        try:
            tfs_bytes = base64.urlsafe_b64decode(tfs_padded)
        except:
            tfs_bytes = base64.b64decode(tfs_padded)

        # Parse protobuf
        query = PB.ReturnFlightQuery()
        query.ParseFromString(tfs_bytes)

        # Validate structure
        if len(query.legs) < 2:
            raise ValueError(f"TFS contains {len(query.legs)} leg(s), expected 2 for round-trip")

        if query.step != 2:
            raise ValueError(f"TFS step is {query.step}, expected 2 (return flight selection)")

        # Extract outbound flight segments (can be multiple for connecting flights)
        outbound_leg = query.legs[0]
        if not outbound_leg.selected_flight:
            raise ValueError("Outbound leg does not have any selected flights")

        outbound_segments = []
        for flight in outbound_leg.selected_flight:
            outbound_segments.append({
                'from_airport': flight.from_airport,
                'to_airport': flight.to_airport,
                'date': flight.date,
                'airline': flight.airline,
                'flight_number': flight.flight_number,
            })

        # For backward compatibility, also provide a single 'outbound' dict with the first segment
        outbound = outbound_segments[0] if outbound_segments else None

        # Extract return flight segments (if selected)
        return_leg = query.legs[1]
        return_flight = None
        return_segments = []

        if return_leg.selected_flight:
            for flight in return_leg.selected_flight:
                return_segments.append({
                    'from_airport': flight.from_airport,
                    'to_airport': flight.to_airport,
                    'date': flight.date,
                    'airline': flight.airline,
                    'flight_number': flight.flight_number,
                })
            # For backward compatibility, also provide single 'return' dict with first segment
            return_flight = return_segments[0] if return_segments else None

        return {
            'query_type': query.query_type,
            'step': query.step,
            'outbound': outbound,  # First segment for backward compatibility
            'outbound_segments': outbound_segments,  # All segments
            'return': return_flight,  # First segment for backward compatibility
            'return_segments': return_segments,  # All segments
        }

    except Exception as e:
        raise ValueError(f"Failed to decode return flight TFS: {e}")


def get_return_flight_options(
    return_search_tfs: str,
    *,
    mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "fallback",
    currency: str = "",
    tfu: str = "EgQIABABIgA",
) -> List[ReturnFlightOption]:
    """Fetch and decode all return flight options for a given outbound selection.

    This function:
    1. Fetches the return flight selection page using the provided TFS
    2. Parses flight options using JS data source (includes flight numbers)
    3. Falls back to HTML if JS parsing fails (no flight numbers)
    4. Returns flight details with all available information

    Args:
        return_search_tfs: TFS string from create_return_flight_filter()
        mode: Fetch mode (default: 'fallback' for best reliability)
              All modes now work with JS data source for return flights
        currency: Currency code for prices (default: "")
        tfu: TFU parameter from selected outbound itinerary (default: "EgQIABABIgA")
             Pass selected_itinerary.tfu to preserve it through the booking flow

    Returns:
        List[ReturnFlightOption]: List of return flight options with available details
        - JS data source: Includes flight numbers, aircraft type, detailed timing
        - HTML fallback: All details except flight numbers (if JS parsing fails)

    Raises:
        RuntimeError: If unable to fetch or parse return flights

    Example:
        >>> from fast_flights import create_return_flight_filter, get_return_flight_options
        >>>
        >>> # After user selects outbound flight
        >>> selected_outbound = outbound_results.best[0]
        >>> tfs = create_return_flight_filter(
        ...     outbound_date="2025-11-18",
        ...     outbound_from="SFO",
        ...     outbound_to="MCO",
        ...     outbound_airline="UA",
        ...     outbound_flight_number="2230",
        ...     return_date="2025-11-25"
        ... )
        >>>
        >>> # Get all return flight options, passing tfu from selected outbound
        >>> options = get_return_flight_options(tfs, tfu=selected_outbound.tfu)
        >>>
        >>> for option in options:
        ...     print(f"{option.airline} {option.flight_number}: ${option.total_price}")
    """
    from .core import get_flights_from_tfs

    # Decode the search TFS to get outbound flight info
    search_details = decode_return_flight_tfs(return_search_tfs)
    outbound_info = search_details['outbound']

    # Try JS data source first (provides flight numbers when it works)
    result_js = None
    try:
        result_js = get_flights_from_tfs(
            return_search_tfs,
            data_source='js',
            mode=mode,
            currency=currency,
            tfu=tfu
        )
    except:
        pass  # Will fall back to HTML

    # If JS worked and has the expected structure, use it
    if result_js and hasattr(result_js, 'best'):
        return_options = []
        all_itineraries = result_js.best + result_js.other

        for itinerary in all_itineraries:
            if not itinerary.flights or len(itinerary.flights) == 0:
                continue

            first_flight = itinerary.flights[0]

            # Format times safely, handling missing data and None values
            dep_time = ""
            if (first_flight.departure_time and len(first_flight.departure_time) >= 2
                and first_flight.departure_time[0] is not None and first_flight.departure_time[1] is not None):
                dep_time = f"{first_flight.departure_time[0]:02d}:{first_flight.departure_time[1]:02d}"

            arr_time = ""
            if (first_flight.arrival_time and len(first_flight.arrival_time) >= 2
                and first_flight.arrival_time[0] is not None and first_flight.arrival_time[1] is not None):
                arr_time = f"{first_flight.arrival_time[0]:02d}:{first_flight.arrival_time[1]:02d}"

            dep_date = ""
            if (first_flight.departure_date and len(first_flight.departure_date) >= 3
                and first_flight.departure_date[0] is not None and first_flight.departure_date[1] is not None
                and first_flight.departure_date[2] is not None):
                dep_date = f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}"

            option = ReturnFlightOption(
                airline=first_flight.airline,
                flight_number=first_flight.flight_number,
                departure_airport=itinerary.departure_airport,
                arrival_airport=itinerary.arrival_airport,
                departure_date=dep_date,
                departure_time=dep_time,
                arrival_time=arr_time,
                duration_minutes=itinerary.travel_time,
                stops=len(itinerary.flights) - 1,
                total_price=itinerary.itinerary_summary.price if itinerary.itinerary_summary else 0.0,
                currency=itinerary.itinerary_summary.currency if itinerary.itinerary_summary else currency,
                aircraft=first_flight.aircraft if hasattr(first_flight, 'aircraft') else None,
                tfs="",
                raw_itinerary=itinerary,
            )

            return_options.append(option)

        return return_options

    # Fall back to HTML data source with force-fallback to render JavaScript
    result_html = get_flights_from_tfs(
        return_search_tfs,
        data_source='html',
        mode=mode,  # Use the same mode as specified (fallback/force-fallback/local/bright-data)
        currency=currency,
        tfu=tfu
    )

    if result_html is None or not hasattr(result_html, 'flights'):
        raise RuntimeError("No return flights found")

    return_options = []

    for flight in result_html.flights:
        # Parse the flight name to extract airline (HTML doesn't provide flight numbers)
        # Name format is usually like "United" or "Alaska"
        airline_name = flight.name

        # Parse times from strings like "6:30 AM on Tue, Nov 25"
        # Departure format: "H:MM AM/PM on Day, Mon DD"
        dep_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', flight.departure)
        arr_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', flight.arrival)

        departure_time = dep_match.group(1) if dep_match else flight.departure
        arrival_time = arr_match.group(1) if arr_match else flight.arrival

        # Parse duration like "6 hr 8 min"
        duration_match = re.search(r'(\d+)\s*hr\s*(\d+)\s*min', flight.duration)
        if duration_match:
            hours = int(duration_match.group(1))
            minutes = int(duration_match.group(2))
            duration_minutes = hours * 60 + minutes
        else:
            # Try just hours
            duration_match = re.search(r'(\d+)\s*hr', flight.duration)
            duration_minutes = int(duration_match.group(1)) * 60 if duration_match else 0

        # Parse price like "$887"
        price_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', flight.price)
        price = float(price_match.group(1).replace(',', '')) if price_match else 0.0

        option = ReturnFlightOption(
            airline=airline_name,
            flight_number="",  # HTML doesn't provide flight numbers
            departure_airport=outbound_info['to_airport'],  # Return from outbound destination
            arrival_airport=outbound_info['from_airport'],  # Return to outbound origin
            departure_date=search_details['return']['date'] if search_details['return'] else "",
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration_minutes=duration_minutes,
            stops=flight.stops,
            total_price=price,
            currency=currency or "USD",
            aircraft=None,  # HTML doesn't provide aircraft type
            tfs="",
            raw_itinerary=None,
        )

        return_options.append(option)

    return return_options
