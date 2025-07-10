#!/usr/bin/env python3.11
"""Debug script to find United + Air Canada flights with airport name inconsistency"""

import json
from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter

def debug_specific_flight():
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
    print("Fetching flight data...")
    result = get_flights_from_filter(filter_data)
    
    print(f"\nFound {len(result.flights)} flights")
    
    # Look specifically for United + Air Canada flights
    for i, flight in enumerate(result.flights):
        if "United" in flight.name and "Air Canada" in flight.name:
            print(f"\n{'='*60}")
            print(f"Found United + Air Canada flight: {flight.name}")
            print(f"Main flight airports: {flight.departure_airport} -> {flight.arrival_airport}")
            print(f"Flight number: {flight.flight_number}")
            print(f"Price: ${flight.price}")
            
            if flight.connections:
                print(f"\nConnections ({len(flight.connections)}):")
                for j, conn in enumerate(flight.connections):
                    print(f"\n  Connection {j+1}:")
                    print(f"    Flight: {conn.flight_number}")
                    print(f"    Name: {conn.name}")
                    print(f"    Departure Airport: {conn.departure_airport!r} (length: {len(conn.departure_airport or '')})")
                    print(f"    Arrival Airport: {conn.arrival_airport!r} (length: {len(conn.arrival_airport or '')})")
                    
                    # Check if these look like codes or names
                    if conn.departure_airport and len(conn.departure_airport) > 4:
                        print(f"    ⚠️  ISSUE: Departure airport is a name, not a code!")
                    if conn.arrival_airport and len(conn.arrival_airport) > 4:
                        print(f"    ⚠️  ISSUE: Arrival airport is a name, not a code!")
            
            # Output full JSON
            print(f"\nFull flight JSON:")
            flight_dict = {
                'name': flight.name,
                'departure_airport': flight.departure_airport,
                'arrival_airport': flight.arrival_airport,
                'connections': [
                    {
                        'name': c.name,
                        'flight_number': c.flight_number,
                        'departure_airport': c.departure_airport,
                        'arrival_airport': c.arrival_airport,
                    } for c in flight.connections
                ] if flight.connections else None
            }
            print(json.dumps(flight_dict, indent=2))
    
    # Also look for any flight with airport name issues
    print(f"\n\n{'='*60}")
    print("Checking ALL flights for airport name issues...")
    
    issues_found = 0
    for i, flight in enumerate(result.flights):
        if flight.connections:
            for j, conn in enumerate(flight.connections):
                if (conn.departure_airport and len(conn.departure_airport) > 4) or \
                   (conn.arrival_airport and len(conn.arrival_airport) > 4):
                    if issues_found == 0:
                        print(f"\nFlights with airport name issues:")
                    issues_found += 1
                    print(f"\n{issues_found}. {flight.name} (${flight.price})")
                    print(f"   Connection: {conn.flight_number}")
                    print(f"   Departure: {conn.departure_airport!r}")
                    print(f"   Arrival: {conn.arrival_airport!r}")
                    
                    # Stop after finding 5 examples
                    if issues_found >= 5:
                        print("\n... (showing first 5 examples)")
                        return

if __name__ == "__main__":
    debug_specific_flight()