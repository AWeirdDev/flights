#!/usr/bin/env python3.11
"""
Verify that the aircraft fix works for direct flights.
"""

import json
from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter

def test_direct_flight_aircraft():
    print("Testing aircraft data fix for direct flights...\n")
    
    # Test with the same route the user mentioned (GCM -> JFK)
    filter_data = create_filter(
        flight_data=[
            FlightData(
                date="2025-08-06",
                from_airport="GCM",
                to_airport="JFK",
            ),
        ],
        trip="one-way",
        passengers=Passengers(adults=1),
        seat="economy",
        max_stops=None  # Allow any flights
    )
    
    print(f"Testing route: GCM -> JFK")
    print(f"Filter URL: https://www.google.com/travel/flights?tfs={filter_data.as_b64().decode('utf-8')}")
    print("-" * 80)
    
    # Get flights using Bright Data with hybrid mode
    result = get_flights_from_filter(filter_data, mode="bright-data", data_source='hybrid')
    
    if not result:
        print("No flights found.")
        return
    
    print(f"Found {len(result.flights)} total flights\n")
    
    # Check direct flights
    direct_flights = [f for f in result.flights if f.stops == 0]
    direct_with_aircraft = [f for f in direct_flights if f.aircraft_details]
    
    print(f"Direct flights: {len(direct_flights)}")
    print(f"Direct flights with aircraft data: {len(direct_with_aircraft)}")
    
    # Show first few direct flights
    print("\nFirst 5 direct flights:")
    for i, flight in enumerate(direct_flights[:5], 1):
        print(f"\nDirect Flight {i}:")
        print(f"  Flight: {flight.flight_number}")
        print(f"  Airline: {flight.name}")
        print(f"  Route: {flight.departure_airport} -> {flight.arrival_airport}")
        print(f"  Aircraft: {flight.aircraft_details if flight.aircraft_details else 'MISSING!'}")
        print(f"  Price: ${flight.price}")
    
    # Also test LAX -> JFK for more results
    print("\n" + "="*80)
    print("Testing route: LAX -> JFK")
    print("="*80)
    
    filter_data2 = create_filter(
        flight_data=[
            FlightData(
                date="2025-08-06",
                from_airport="LAX",
                to_airport="JFK",
            ),
        ],
        trip="one-way",
        passengers=Passengers(adults=1),
        seat="economy",
        max_stops=0  # Direct flights only
    )
    
    result2 = get_flights_from_filter(filter_data2, mode="bright-data", data_source='hybrid')
    
    if result2:
        direct_count = len(result2.flights)
        with_aircraft = sum(1 for f in result2.flights if f.aircraft_details)
        
        print(f"\nDirect flights found: {direct_count}")
        print(f"With aircraft data: {with_aircraft}")
        
        if with_aircraft == direct_count:
            print("\n✅ SUCCESS: All direct flights now have aircraft data!")
        else:
            print(f"\n❌ ISSUE: {direct_count - with_aircraft} flights still missing aircraft data")
        
        # Show sample
        if result2.flights:
            sample = result2.flights[0]
            print(f"\nSample direct flight:")
            print(json.dumps({
                "is_best": sample.is_best,
                "name": sample.name,
                "departure": sample.departure,
                "arrival": sample.arrival,
                "arrival_time_ahead": sample.arrival_time_ahead,
                "duration": sample.duration,
                "stops": sample.stops,
                "delay": sample.delay,
                "price": sample.price,
                "flight_number": sample.flight_number,
                "departure_airport": sample.departure_airport,
                "arrival_airport": sample.arrival_airport,
                "connecting_airports": sample.connecting_airports,
                "connections": sample.connections,
                "emissions": sample.emissions,
                "operated_by": sample.operated_by,
                "aircraft_details": sample.aircraft_details
            }, indent=2))

if __name__ == "__main__":
    test_direct_flight_aircraft()