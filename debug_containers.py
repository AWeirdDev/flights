#!/usr/bin/env python3
"""
Debug containers to understand round-trip structure
"""

import os
import re
from datetime import datetime, timedelta
from fast_flights import create_filter, FlightData, Passengers
from fast_flights.filter import TFSData
from fast_flights.bright_data_fetch import bright_data_fetch
from selectolax.lexbor import LexborHTMLParser

# Test configuration
test_date = datetime.now() + timedelta(days=30)
return_date = test_date + timedelta(days=7)

# Create a round-trip filter
filter = TFSData.from_interface(
    flight_data=[
        FlightData(
            date=test_date.strftime("%Y-%m-%d"),
            from_airport="JFK",
            to_airport="LAX",
        ),
        FlightData(
            date=return_date.strftime("%Y-%m-%d"),
            from_airport="LAX",
            to_airport="JFK",
        )
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
)

data = filter.as_b64()
params = {
    "tfs": data.decode("utf-8"),
    "hl": "en",
    "tfu": "EgQIABABIgA",
    "curr": "",
}

print("Fetching flights...")
res = bright_data_fetch(params)
parser = LexborHTMLParser(res.text)

# Get all flight containers
flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
print(f"\nFound {len(flight_containers)} containers")

for container_idx, container in enumerate(flight_containers):
    jsname = container.attributes.get('jsname', 'Unknown')
    flight_items = container.css("ul.Rk10dc li")
    
    print(f"\nContainer {container_idx} (jsname={jsname}): {len(flight_items)} items")
    print("-" * 60)
    
    # Look at first 3 items in each container
    for item_idx, item in enumerate(flight_items[:3]):
        print(f"\n  Item {item_idx + 1}:")
        
        # Extract URL to see route info
        url_elem = item.css_first('[data-travelimpactmodelwebsiteurl]')
        if url_elem:
            url = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
            if url:
                print(f"    URL: {url}")
                # Extract route info from URL
                route_match = re.search(r'itinerary=([A-Z0-9,-]+)', url)
                if route_match:
                    itinerary = route_match.group(1)
                    print(f"    Itinerary: {itinerary}")
                    
                    # Parse first segment to understand direction
                    first_segment = itinerary.split(',')[0]
                    parts = first_segment.split('-')
                    if len(parts) >= 2:
                        print(f"    Route: {parts[0]} → {parts[1]}")
        
        # Check aria-label for additional info
        aria_label = item.attributes.get('aria-label', '')
        if not aria_label:
            main_container = item.css_first('.JMc5Xc')
            if main_container:
                aria_label = main_container.attributes.get('aria-label', '')
        
        if aria_label:
            # Extract key info from aria-label
            if 'from' in aria_label.lower() and 'to' in aria_label.lower():
                print(f"    Aria-label snippet: {aria_label[:100]}...")
        
        # Get departure/arrival divs
        departure_elem = item.css_first('div.G2WY5c div')
        arrival_elem = item.css_first('div.c8rWCd div')
        
        if departure_elem:
            print(f"    Departure elem: {departure_elem.text(strip=True)}")
        if arrival_elem:
            print(f"    Arrival elem: {arrival_elem.text(strip=True)}")

print("\nSummary:")
for i, container in enumerate(flight_containers):
    jsname = container.attributes.get('jsname', 'Unknown')
    count = len(container.css("ul.Rk10dc li"))
    print(f"  Container {i} ({jsname}): {count} flights")