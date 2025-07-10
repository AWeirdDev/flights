#!/usr/bin/env python3.11
"""Debug script to trace airport formatting inconsistency in flight connections"""

import json
from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter

def debug_flight_data():
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
    
    # Look for flights with connections
    for i, flight in enumerate(result.flights):
        if flight.connections and len(flight.connections) > 0:
            print(f"\n{'='*60}")
            print(f"Flight {i+1}: {flight.name}")
            print(f"Main flight airports: {flight.departure_airport} -> {flight.arrival_airport}")
            print(f"Flight number: {flight.flight_number}")
            
            print(f"\nConnections ({len(flight.connections)}):")
            for j, conn in enumerate(flight.connections):
                print(f"\n  Connection {j+1}:")
                print(f"    Flight: {conn.flight_number}")
                print(f"    Departure Airport: {conn.departure_airport!r}")
                print(f"    Arrival Airport: {conn.arrival_airport!r}")
                print(f"    Aircraft: {conn.aircraft}")
                
                # Check if these look like codes or names
                dep_looks_like_code = conn.departure_airport and len(conn.departure_airport) <= 4
                arr_looks_like_code = conn.arrival_airport and len(conn.arrival_airport) <= 4
                
                if not dep_looks_like_code:
                    print(f"    ⚠️  Departure airport appears to be a name, not a code")
                if not arr_looks_like_code:
                    print(f"    ⚠️  Arrival airport appears to be a name, not a code")
            
            # Also check connecting_airports
            if flight.connecting_airports:
                print(f"\nConnecting airports:")
                for airport, duration in flight.connecting_airports:
                    print(f"  {airport}: {duration}")
            
            # Output full JSON for one example
            if i == 0:
                print(f"\nFull JSON for first flight with connections:")
                flight_dict = {
                    'name': flight.name,
                    'departure_airport': flight.departure_airport,
                    'arrival_airport': flight.arrival_airport,
                    'connections': [
                        {
                            'flight_number': c.flight_number,
                            'departure_airport': c.departure_airport,
                            'arrival_airport': c.arrival_airport,
                            'aircraft': c.aircraft
                        } for c in flight.connections
                    ] if flight.connections else None
                }
                print(json.dumps(flight_dict, indent=2))
            
            # Only show first 3 flights with connections
            if i >= 2:
                break

if __name__ == "__main__":
    debug_flight_data()