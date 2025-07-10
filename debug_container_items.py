#!/usr/bin/env python3
"""Debug why we get 109 items instead of 108."""

import sys
from selectolax.lexbor import LexborHTMLParser

# Add the project to path
sys.path.insert(0, '/Users/dave/Work/flights')

from fast_flights.core import should_skip_container, extract_html_enrichments
from fast_flights.flights_impl import FlightData, Passengers
from fast_flights.filter import TFSData
from fast_flights.bright_data_fetch import bright_data_fetch


def main():
    print("=== Debugging Container Items ===\n")
    
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
    
    # Get flight containers
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    container_sizes = [len(container.css("ul.Rk10dc li")) for container in flight_containers]
    
    print(f"Number of containers: {len(flight_containers)}")
    print(f"Container sizes: {container_sizes}")
    print(f"Total items: {sum(container_sizes)}")
    
    # Check which containers are kept
    print("\nContainer processing:")
    total_kept = 0
    for i, size in enumerate(container_sizes):
        skip = should_skip_container(i, container_sizes)
        status = "SKIP" if skip else "KEEP"
        if not skip:
            total_kept += size
        print(f"  Container {i}: {size} items - {status}")
    
    print(f"\nTotal items kept: {total_kept}")
    
    # Now let's see what the HTML parser does
    print("\n=== HTML Parser Behavior ===")
    # Simulate HTML parser logic
    flights_html = []
    for i, fl in enumerate(flight_containers):
        if should_skip_container(i, container_sizes):
            print(f"Container {i}: Skipped")
            continue
            
        items = fl.css("ul.Rk10dc li")
        # HTML parser uses this condition to exclude last item in some cases
        if i == 0:
            items_to_process = items
        else:
            items_to_process = items[:-1]  # Exclude last item
        
        print(f"Container {i}: Processing {len(items_to_process)} of {len(items)} items")
        flights_html.extend(items_to_process)
    
    print(f"\nHTML parser would extract: {len(flights_html)} flights")
    
    # Check enrichment extraction
    print("\n=== Enrichment Extraction ===")
    enrichments = extract_html_enrichments(parser, res.text)
    print(f"Enrichments extracted: {len(enrichments)}")
    
    # Find the issue
    if len(enrichments) == 109:
        print("\nThe issue: extract_html_enrichments extracts all 109 items")
        print("But HTML parser only extracts 108 flights (excludes last item of container 1)")
        print("This causes a mismatch!")


if __name__ == "__main__":
    main()