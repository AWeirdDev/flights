#!/usr/bin/env python3
"""
Test return flights with different routes
"""

import os
from datetime import datetime, timedelta
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers
from fast_flights.filter import TFSData
from fast_flights.bright_data_fetch import bright_data_fetch
from selectolax.lexbor import LexborHTMLParser

test_date = datetime.now() + timedelta(days=30)
return_date = test_date + timedelta(days=7)

print("Testing different round-trip routes")
print("=" * 60)

routes = [
    ("NYC", "LON"),  # New York to London
    ("SFO", "ORD"),  # San Francisco to Chicago
    ("LAX", "JFK"),  # Reverse of original (LAX to JFK and back)
]

for from_airport, to_airport in routes:
    print(f"\nTesting {from_airport} → {to_airport} → {from_airport}")
    print("-" * 40)
    
    filter = TFSData.from_interface(
        flight_data=[
            FlightData(
                date=test_date.strftime("%Y-%m-%d"),
                from_airport=from_airport,
                to_airport=to_airport,
            ),
            FlightData(
                date=return_date.strftime("%Y-%m-%d"),
                from_airport=to_airport,
                to_airport=from_airport,
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
    
    try:
        res = bright_data_fetch(params)
        parser = LexborHTMLParser(res.text)
        
        # Get all flight containers
        flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
        print(f"Found {len(flight_containers)} containers")
        
        # Check first item in each container
        for i, container in enumerate(flight_containers):
            items = container.css("ul.Rk10dc li")
            if items:
                first_item = items[0]
                url_elem = first_item.css_first('[data-travelimpactmodelwebsiteurl]')
                if url_elem:
                    url = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
                    # Extract route from URL
                    import re
                    route_match = re.search(r'itinerary=([A-Z0-9,-]+)', url)
                    if route_match:
                        itinerary = route_match.group(1)
                        parts = itinerary.split(',')[0].split('-')
                        if len(parts) >= 2:
                            print(f"  Container {i}: {parts[0]} → {parts[1]} ({len(items)} flights)")
    
    except Exception as e:
        print(f"Error: {e}")