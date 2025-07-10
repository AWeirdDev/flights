#!/usr/bin/env python3
"""Find where the extra enrichment is coming from."""

import sys
import json
import re
from selectolax.lexbor import LexborHTMLParser

# Add the project to path
sys.path.insert(0, '/Users/dave/Work/flights')

from fast_flights.core import extract_html_enrichments, convert_decoded_to_result
from fast_flights.decoder import ResultDecoder
from fast_flights.flights_impl import FlightData, Passengers
from fast_flights.filter import TFSData
from fast_flights.bright_data_fetch import bright_data_fetch


def main():
    print("=== Finding the Extra Enrichment ===\n")
    
    # Define test flight parameters
    flight_data = [
        FlightData(
            date="2025-08-16",
            from_airport="LAX",
            to_airport="JFK"
        )
    ]
    
    passengers = Passengers(adults=1)
    
    filter_data = TFSData.from_interface(
        flight_data=flight_data,
        trip="one-way",
        passengers=passengers,
        seat="economy",
        max_stops=None
    )
    
    params = {
        "tfs": filter_data.as_b64().decode("utf-8"),
        "hl": "en",
        "tfu": "EgQIABABIgA",
        "curr": "",
    }
    
    res = bright_data_fetch(params)
    parser = LexborHTMLParser(res.text)
    
    # Extract JS data
    script = parser.css_first(r'script.ds\:1').text()
    match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script)
    data = json.loads(match.group(1))
    decoded = ResultDecoder.decode(data)
    js_result = convert_decoded_to_result(decoded)
    
    # Extract HTML enrichments
    html_enrichments = extract_html_enrichments(parser, res.text)
    
    print(f"JS flights: {len(js_result.flights)}")
    print(f"HTML enrichments: {len(html_enrichments)}")
    print(f"Difference: {len(html_enrichments) - len(js_result.flights)}")
    
    # Compare URLs side by side
    print("\n=== Comparing URLs ===")
    print("Index | JS Flight Pattern | Enrichment URL (simplified)")
    print("-" * 80)
    
    for i in range(max(len(js_result.flights), len(html_enrichments))):
        js_pattern = ""
        if i < len(js_result.flights):
            flight = js_result.flights[i]
            if flight.flight_number and flight.departure_airport and flight.arrival_airport:
                flight_num_for_url = flight.flight_number.replace(' ', '-')
                js_pattern = f"{flight.departure_airport}-{flight.arrival_airport}-{flight_num_for_url}"
        
        enrichment_url = ""
        if i < len(html_enrichments) and 'url' in html_enrichments[i]:
            # Extract just the itinerary part
            url = html_enrichments[i]['url']
            match = re.search(r'itinerary=([A-Z0-9,-]+)', url)
            if match:
                enrichment_url = match.group(1)
        
        # Check if they match
        match_status = ""
        if js_pattern and enrichment_url:
            if js_pattern not in enrichment_url:
                match_status = " <-- MISMATCH"
        elif i >= len(js_result.flights):
            match_status = " <-- EXTRA ENRICHMENT"
        elif i >= len(html_enrichments):
            match_status = " <-- MISSING ENRICHMENT"
        
        print(f"{i:5} | {js_pattern:30} | {enrichment_url:50} {match_status}")
        
        # If we find a mismatch, show more details
        if match_status and i < 20:  # Only show details for first 20
            if i < len(js_result.flights):
                flight = js_result.flights[i]
                print(f"      JS: {flight.name} - {flight.flight_number}")
            if i < len(html_enrichments):
                enrich = html_enrichments[i]
                print(f"      Enrichment: arrival_time_ahead={enrich.get('arrival_time_ahead', 'None')}")
    
    # Also check container analysis
    print("\n=== Container Analysis ===")
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    container_sizes = [len(container.css("ul.Rk10dc li")) for container in flight_containers]
    print(f"Container sizes: {container_sizes}")
    print(f"Total items before skip: {sum(container_sizes)}")
    
    # Check what should_skip_container does
    from fast_flights.core import should_skip_container
    items_after_skip = 0
    for i, size in enumerate(container_sizes):
        if not should_skip_container(i, container_sizes):
            items_after_skip += size
    print(f"Total items after skip: {items_after_skip}")


if __name__ == "__main__":
    main()