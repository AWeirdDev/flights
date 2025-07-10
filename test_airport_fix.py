#!/usr/bin/env python3.11
"""Test script to verify the airport code fix works"""

import json
from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter

def test_airport_fix():
    # Create a sample flight search
    filter_data = create_filter(
        flight_data=[
            FlightData(
                date="2025-07-15",
                from_airport="GCM",
                to_airport="LHR",
            ),
        ],
        passengers=Passengers(adults=1),
        max_stops=2,
        trip="one-way",
        seat="economy"
    )
    
    # Get raw flights data
    print("Fetching flight data to test airport fix...")
    result = get_flights_from_filter(filter_data)
    
    print(f"\nFound {len(result.flights)} flights")
    
    # Check for any flights with airport formatting issues
    issues_found = 0
    fixed_count = 0
    
    for i, flight in enumerate(result.flights):
        if flight.connections:
            has_issue = False
            for j, conn in enumerate(flight.connections):
                # Check if airport codes look correct (should be 3-4 chars)
                dep_ok = conn.departure_airport and 2 <= len(conn.departure_airport) <= 4
                arr_ok = conn.arrival_airport and 2 <= len(conn.arrival_airport) <= 4
                
                if not dep_ok or not arr_ok:
                    if not has_issue:
                        issues_found += 1
                        print(f"\n{issues_found}. Flight: {flight.name} (${flight.price})")
                        print(f"   Main route: {flight.departure_airport} -> {flight.arrival_airport}")
                        has_issue = True
                    
                    print(f"\n   Connection {j+1}: {conn.flight_number}")
                    if not dep_ok:
                        print(f"     ❌ Departure: {conn.departure_airport!r} (length: {len(conn.departure_airport or '')})")
                    else:
                        print(f"     ✅ Departure: {conn.departure_airport!r}")
                    
                    if not arr_ok:
                        print(f"     ❌ Arrival: {conn.arrival_airport!r} (length: {len(conn.arrival_airport or '')})")
                    else:
                        print(f"     ✅ Arrival: {conn.arrival_airport!r}")
                else:
                    # Both airports look like codes
                    if j == 0 and i < 5:  # Show first connection of first 5 flights as examples of success
                        fixed_count += 1
                        if fixed_count <= 3:
                            print(f"\n✅ Correctly formatted - Flight: {flight.name}")
                            print(f"   Connection: {conn.flight_number}")
                            print(f"   Departure: {conn.departure_airport!r}")
                            print(f"   Arrival: {conn.arrival_airport!r}")
    
    if issues_found == 0:
        print("\n🎉 Success! No airport formatting issues found.")
        print("All connections use proper airport codes.")
    else:
        print(f"\n⚠️  Found {issues_found} flights with airport formatting issues.")
    
    # Show a specific example if we find United + Air Canada
    print("\n" + "="*60)
    print("Looking for United + Air Canada flights specifically...")
    
    for flight in result.flights:
        if "United" in flight.name and "Air Canada" in flight.name and flight.connections:
            print(f"\nFound: {flight.name}")
            print(f"Price: ${flight.price}")
            print("\nConnections:")
            for i, conn in enumerate(flight.connections):
                print(f"\n  {i+1}. {conn.flight_number} ({conn.name})")
                print(f"     {conn.departure_airport} -> {conn.arrival_airport}")
            
            # Output JSON
            print("\nJSON representation:")
            flight_dict = {
                'name': flight.name,
                'departure_airport': flight.departure_airport,
                'arrival_airport': flight.arrival_airport,
                'connections': [
                    {
                        'flight_number': c.flight_number,
                        'departure_airport': c.departure_airport,
                        'arrival_airport': c.arrival_airport,
                    } for c in flight.connections
                ]
            }
            print(json.dumps(flight_dict, indent=2))
            break

if __name__ == "__main__":
    test_airport_fix()