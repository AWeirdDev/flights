#!/usr/bin/env python3
"""
Test to verify the filter construction for round-trip flights
"""

import base64
import json
from datetime import datetime, timedelta
from fast_flights import create_filter, FlightData, Passengers
from fast_flights.filter import TFSData

# Test configuration
test_date = datetime.now() + timedelta(days=30)
return_date = test_date + timedelta(days=7)

# Create a round-trip filter
filter = create_filter(
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
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
    max_stops=None,
)

print("Round-Trip Filter Analysis")
print("=" * 60)

# Get the base64 encoded filter
b64_filter = filter.as_b64().decode('utf-8')
print(f"Base64 Filter: {b64_filter}")
print(f"Google Flights URL: https://www.google.com/travel/flights?tfs={b64_filter}")

# Decode the base64 to see the actual data
decoded = base64.b64decode(b64_filter)
print(f"\nDecoded bytes: {decoded}")
print(f"Length: {len(decoded)} bytes")

# Try to understand the structure
print("\n--- Filter Structure ---")
print(f"Trip type: round-trip")
print(f"Outbound: {test_date.strftime('%Y-%m-%d')} JFK → LAX")
print(f"Return: {return_date.strftime('%Y-%m-%d')} LAX → JFK")

# Create a one-way filter for comparison
one_way_filter = create_filter(
    flight_data=[
        FlightData(
            date=test_date.strftime("%Y-%m-%d"),
            from_airport="JFK",
            to_airport="LAX",
        )
    ],
    trip="one-way",
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
    max_stops=None,
)

b64_one_way = one_way_filter.as_b64().decode('utf-8')
print(f"\nOne-way filter for comparison: {b64_one_way}")
print(f"One-way URL: https://www.google.com/travel/flights?tfs={b64_one_way}")

# Check if the round-trip filter contains both segments
if b"JFK" in decoded and b"LAX" in decoded:
    print("\n✓ Both airports found in filter")
    jfk_count = decoded.count(b"JFK")
    lax_count = decoded.count(b"LAX")
    print(f"  JFK occurrences: {jfk_count}")
    print(f"  LAX occurrences: {lax_count}")
else:
    print("\n✗ Missing airport codes in filter")