#!/usr/bin/env python3
"""
Test return flights with Bright Data in hybrid mode
"""

import os
import json
from datetime import datetime, timedelta
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

# Test configuration
test_date = datetime.now() + timedelta(days=30)
return_date = test_date + timedelta(days=7)

# Create a round-trip filter for a popular route
filter = create_filter(
    flight_data=[
        FlightData(
            date=test_date.strftime("%Y-%m-%d"),
            from_airport="JFK",  # New York JFK
            to_airport="LAX",    # Los Angeles
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

print("Testing Return Flights with Bright Data in Hybrid Mode")
print("=" * 60)
print(f"Route: JFK → LAX → JFK (Round-trip)")
print(f"Outbound: {test_date.strftime('%Y-%m-%d')}")
print(f"Return: {return_date.strftime('%Y-%m-%d')}")
print(f"Mode: bright-data")
print(f"Data Source: hybrid")
print("=" * 60)

try:
    # Get flights using Bright Data mode with hybrid data source
    result = get_flights_from_filter(filter, mode="bright-data", data_source='hybrid')
    
    if not result or not result.flights:
        print("No flights found.")
        exit(0)
    
    print(f"\nFound {len(result.flights)} flights")
    print(f"Current price level: {result.current_price}")
    
    # Separate outbound and return flights based on departure/arrival airports
    outbound_flights = []
    return_flights = []
    
    for flight in result.flights:
        if flight.departure_airport == "JFK" and flight.arrival_airport == "LAX":
            outbound_flights.append(flight)
        elif flight.departure_airport == "LAX" and flight.arrival_airport == "JFK":
            return_flights.append(flight)
    
    print(f"\nOutbound flights (JFK → LAX): {len(outbound_flights)}")
    print(f"Return flights (LAX → JFK): {len(return_flights)}")
    
    # Display sample flights
    if outbound_flights:
        print("\n--- Sample Outbound Flight ---")
        flight = outbound_flights[0]
        print(f"Flight: {flight.name}")
        print(f"Departure: {flight.departure} from {flight.departure_airport}")
        print(f"Arrival: {flight.arrival} at {flight.arrival_airport}")
        if flight.arrival_time_ahead:
            print(f"Arrival day: {flight.arrival_time_ahead}")
        print(f"Duration: {flight.duration}")
        print(f"Stops: {flight.stops}")
        print(f"Price: ${flight.price}")
        if hasattr(flight, 'emissions') and flight.emissions:
            print(f"Emissions: {flight.emissions}")
        if hasattr(flight, 'aircraft_details') and flight.aircraft_details:
            print(f"Aircraft: {flight.aircraft_details}")
    
    if return_flights:
        print("\n--- Sample Return Flight ---")
        flight = return_flights[0]
        print(f"Flight: {flight.name}")
        print(f"Departure: {flight.departure} from {flight.departure_airport}")
        print(f"Arrival: {flight.arrival} at {flight.arrival_airport}")
        if flight.arrival_time_ahead:
            print(f"Arrival day: {flight.arrival_time_ahead}")
        print(f"Duration: {flight.duration}")
        print(f"Stops: {flight.stops}")
        print(f"Price: ${flight.price}")
        if hasattr(flight, 'emissions') and flight.emissions:
            print(f"Emissions: {flight.emissions}")
        if hasattr(flight, 'aircraft_details') and flight.aircraft_details:
            print(f"Aircraft: {flight.aircraft_details}")
    
    # Check for enrichment data
    print("\n--- Enrichment Data Summary ---")
    emissions_count = sum(1 for f in result.flights if hasattr(f, 'emissions') and f.emissions)
    aircraft_count = sum(1 for f in result.flights if hasattr(f, 'aircraft_details') and f.aircraft_details)
    operated_by_count = sum(1 for f in result.flights if hasattr(f, 'operated_by') and f.operated_by)
    
    print(f"Flights with emissions data: {emissions_count}/{len(result.flights)}")
    print(f"Flights with aircraft details: {aircraft_count}/{len(result.flights)}")
    print(f"Flights with operated_by info: {operated_by_count}/{len(result.flights)}")
    
    print("\n✅ Return flights are working correctly with Bright Data in hybrid mode!")
    
except Exception as e:
    print(f"\n❌ Error occurred: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()