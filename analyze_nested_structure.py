#!/usr/bin/env python3
"""Analyze nested structure in more detail."""

import sys
import json
import re
from selectolax.lexbor import LexborHTMLParser

# Add the project to path
sys.path.insert(0, '/Users/dave/Work/flights')

from fast_flights.core import extract_html_enrichments, convert_decoded_to_result, should_skip_container
from fast_flights.decoder import ResultDecoder
from fast_flights.flights_impl import FlightData, Passengers
from fast_flights.filter import TFSData
from fast_flights.bright_data_fetch import bright_data_fetch


def main():
    print("=== Deep Analysis of Nested Structure ===\n")
    
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
    
    # Extract JS data for comparison
    script = parser.css_first(r'script.ds\:1').text()
    match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script)
    data = json.loads(match.group(1))
    decoded = ResultDecoder.decode(data)
    js_result = convert_decoded_to_result(decoded)
    
    print(f"JS Result: {len(js_result.flights)} flights\n")
    
    # Analyze container structure
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    container_sizes = [len(container.css("ul.Rk10dc li")) for container in flight_containers]
    
    print("Container Analysis:")
    print(f"Container jsnames: {[c.attributes.get('jsname', '') for c in flight_containers]}")
    print(f"Container sizes: {container_sizes}")
    print(f"Pattern: IWWDBc='best', YdtKid='other'\n")
    
    # Analyze flights in detail
    print("Flight Structure Analysis:")
    flight_idx = 0
    
    for cont_idx, container in enumerate(flight_containers):
        if should_skip_container(cont_idx, container_sizes):
            print(f"\nContainer {cont_idx} (SKIPPED - duplicate)")
            continue
            
        container_type = "BEST" if container.attributes.get('jsname') == 'IWWDBc' else "OTHER"
        print(f"\nContainer {cont_idx} ({container_type}):")
        
        flight_items = container.css("ul.Rk10dc li")
        items_to_process = flight_items if cont_idx == 0 else flight_items[:-1]
        
        # Look at first few flights in this container
        for item_idx, item in enumerate(items_to_process[:3]):
            print(f"\n  Flight {flight_idx} (container {cont_idx}, item {item_idx}):")
            
            # Look for aria-label on the item or its children
            aria_label = item.attributes.get('aria-label', '')
            if not aria_label:
                # Check div.JMc5Xc for aria-label
                main_div = item.css_first('div.JMc5Xc')
                if main_div:
                    aria_label = main_div.attributes.get('aria-label', '')
            
            if aria_label:
                # Extract key info from aria-label
                print(f"    Aria-label: {aria_label[:150]}...")
                
                # Try to extract flight numbers
                flight_pattern = r'([A-Z]{2,3})\s*(\d{1,4})'
                flights_in_label = re.findall(flight_pattern, aria_label)
                if flights_in_label:
                    print(f"    Flights found in aria: {[f'{a} {b}' for a, b in flights_in_label]}")
            
            # Look for URL
            url_elem = item.css_first('[data-travelimpactmodelwebsiteurl]')
            if url_elem:
                url = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
                itinerary_match = re.search(r'itinerary=([^&]+)', url)
                if itinerary_match:
                    print(f"    URL itinerary: {itinerary_match.group(1)}")
            
            # Compare with JS data
            if flight_idx < len(js_result.flights):
                js_flight = js_result.flights[flight_idx]
                print(f"    JS flight: {js_flight.flight_number} ({js_flight.departure_airport}-{js_flight.arrival_airport})")
                print(f"    JS is_best: {js_flight.is_best}")
            
            flight_idx += 1
    
    print("\n\nKey Insights:")
    print("1. Container jsname='IWWDBc' contains 'best' flights (matches JS is_best=True)")
    print("2. Container jsname='YdtKid' contains 'other' flights (matches JS is_best=False)")
    print("3. This gives us a structural hint for matching!")
    print("4. Within each category, we can use more targeted matching")
    
    print("\n\nProposed Better Matching Algorithm:")
    print("""
def match_flights_structurally(js_result, parser):
    # Separate JS flights by is_best flag
    js_best = [f for f in js_result.flights if f.is_best]
    js_other = [f for f in js_result.flights if not f.is_best]
    
    # Get HTML containers by type
    best_container = parser.css_first('div[jsname="IWWDBc"]')
    other_container = parser.css_first('div[jsname="YdtKid"]') 
    
    # Extract enrichments separately for each container
    best_enrichments = extract_from_container(best_container)
    other_enrichments = extract_from_container(other_container)
    
    # Match within each category - much smaller search space!
    matched_best = match_within_category(js_best, best_enrichments)
    matched_other = match_within_category(js_other, other_enrichments)
    
    return matched_best + matched_other
    """)


if __name__ == "__main__":
    main()