#!/usr/bin/env python3
"""
Test file for Bright Data integration with fast-flights
Requires BRIGHT_DATA_API_KEY environment variable to be set
"""

import os
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    print("Usage: export BRIGHT_DATA_API_KEY='your-api-key'")
    print("\nOptional environment variables:")
    print("  BRIGHT_DATA_API_URL (defaults to: https://api.brightdata.com/request)")
    print("  BRIGHT_DATA_SERP_ZONE (defaults to: serp_api1)")
    exit(1)

# Create a filter for testing
filter = create_filter(
    flight_data=[
        FlightData(
            date="2025-08-06",
            from_airport="JFK",  # New York
            to_airport="LAX",    # Los Angeles
        ),
        FlightData(
            date="2025-08-10",
            from_airport="LAX",
            to_airport="JFK",
        )
    ],
    trip="round-trip",
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
    max_stops=None,  # Any number of stops
)

print("Testing Bright Data integration...")
print(f"Filter URL: https://www.google.com/travel/flights?tfs={filter.as_b64().decode('utf-8')}")
print(f"Using Bright Data API URL: {os.environ.get('BRIGHT_DATA_API_URL', 'https://api.brightdata.com/request')}")
print(f"Using zone: {os.environ.get('BRIGHT_DATA_SERP_ZONE', 'serp_api1')}")
print("-" * 80)

try:
    # Get flights using Bright Data mode
    result = get_flights_from_filter(filter, mode="bright-data")
    
    print(f"Current price: {result.current_price}")
    print(f"Found {len(result.flights)} flights\n")
    
    # Display flight results
    for i, flight in enumerate(result.flights, 1):
        print(f"Flight {i}:")
        print(f"  Airline: {flight.name}")
        print(f"  Departure: {flight.departure}")
        print(f"  Arrival: {flight.arrival}")
        print(f"  Duration: {flight.duration}")
        print(f"  Stops: {flight.stops}")
        print(f"  Price: {flight.price}")
        if flight.delay:
            print(f"  Delay: {flight.delay}")
        if flight.is_best:
            print("  ⭐ Best flight")
        print()
        
except Exception as e:
    print(f"Error occurred: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()