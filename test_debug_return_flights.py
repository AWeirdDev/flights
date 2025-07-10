#!/usr/bin/env python3
"""
Debug test for return flights
"""

import os
from datetime import datetime, timedelta
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

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
    passengers=Passengers(adults=1),
    seat="economy",
)

print("Testing Return Flights - Debug Mode")
print("=" * 60)
print(f"Route: JFK → LAX → JFK (Round-trip)")
print(f"Outbound: {test_date.strftime('%Y-%m-%d')}")
print(f"Return: {return_date.strftime('%Y-%m-%d')}")
print("=" * 60)

# Get flights using HTML data source
result = get_flights_from_filter(filter, mode="bright-data", data_source='html')

if not result or not result.flights:
    print("No flights found.")
    exit(0)

print(f"\nFound {len(result.flights)} total flights")

# Analyze all flights
outbound_count = 0
return_count = 0
unknown_count = 0

print("\nAnalyzing flights:")
print("-" * 80)

for i, flight in enumerate(result.flights):
    if flight.departure_airport == "JFK" and flight.arrival_airport == "LAX":
        flight_type = "OUTBOUND"
        outbound_count += 1
    elif flight.departure_airport == "LAX" and flight.arrival_airport == "JFK":
        flight_type = "RETURN"
        return_count += 1
    else:
        flight_type = "UNKNOWN"
        unknown_count += 1
    
    print(f"Flight {i+1}: {flight_type}")
    print(f"  Name: {flight.name}")
    print(f"  Route: {flight.departure_airport} → {flight.arrival_airport}")
    print(f"  Flight #: {flight.flight_number}")
    print(f"  Departure: {flight.departure}")
    print(f"  Arrival: {flight.arrival}")
    print(f"  Price: ${flight.price}")
    print(f"  Is Best: {flight.is_best}")
    
    if i >= 10 and flight_type == "OUTBOUND":
        # Skip printing all outbound flights to focus on finding return flights
        continue
    
    print()

print("-" * 80)
print(f"\nSummary:")
print(f"  Outbound flights (JFK → LAX): {outbound_count}")
print(f"  Return flights (LAX → JFK): {return_count}")
print(f"  Unknown routes: {unknown_count}")

# Check the last few flights to see if they might be return flights
print("\nChecking last 5 flights:")
for i, flight in enumerate(result.flights[-5:]):
    print(f"\nFlight {len(result.flights) - 5 + i + 1}:")
    print(f"  Route: {flight.departure_airport} → {flight.arrival_airport}")
    print(f"  Name: {flight.name}")
    print(f"  Flight #: {flight.flight_number}")
    print(f"  Is Best: {flight.is_best}")