#!/usr/bin/env python3.11
"""Final test to show the fix works with the same JSON format as user's example"""

import json
from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter

def test_final_format():
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
    print("Testing final format...")
    result = get_flights_from_filter(filter_data)
    
    # Find a multi-stop flight to show the format
    for flight in result.flights:
        if flight.connections and len(flight.connections) >= 2:
            # Convert to the same format as user's example
            flight_data = {
                "is_best": flight.is_best,
                "name": flight.name,
                "departure": flight.departure,
                "arrival": flight.arrival,
                "arrival_time_ahead": flight.arrival_time_ahead,
                "duration": flight.duration,
                "stops": flight.stops,
                "delay": flight.delay,
                "price": flight.price,
                "flight_number": flight.flight_number,
                "departure_airport": flight.departure_airport,
                "arrival_airport": flight.arrival_airport,
                "connecting_airports": flight.connecting_airports,
                "connections": [
                    f"Connection(departure='{c.departure}', arrival='{c.arrival}', arrival_time_ahead='{c.arrival_time_ahead}', duration='{c.duration}', name='{c.name}', delay={c.delay}, flight_number='{c.flight_number}', departure_airport='{c.departure_airport}', arrival_airport='{c.arrival_airport}', aircraft='{c.aircraft}', operated_by={c.operated_by})"
                    for c in flight.connections
                ] if flight.connections else None,
                "emissions": flight.emissions,
                "operated_by": flight.operated_by,
                "aircraft_details": flight.aircraft_details
            }
            
            print("Example flight in user's format:")
            print(json.dumps(flight_data, indent=2))
            
            # Check if all airports are codes
            all_good = True
            for conn in flight.connections:
                if len(conn.departure_airport) > 4 or len(conn.arrival_airport) > 4:
                    all_good = False
                    break
            
            if all_good:
                print("\n✅ All airport fields contain proper codes (not names)!")
            else:
                print("\n❌ Some airport fields still contain names instead of codes.")
            
            break

if __name__ == "__main__":
    test_final_format()