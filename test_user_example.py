#!/usr/bin/env python3.11
"""
Test the exact flight from the user's example to ensure it now has aircraft details.
"""

import json
from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter

def main():
    print("Testing the exact flight from user's example (KX 792 GCM->JFK)...\n")
    
    # Create filter matching user's example
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
        max_stops=None
    )
    
    # Get flights
    result = get_flights_from_filter(filter_data, mode="bright-data")
    
    if not result:
        print("No flights found.")
        return
    
    # Find the KX 792 flight
    kx792 = None
    for flight in result.flights:
        if flight.flight_number == "KX 792":
            kx792 = flight
            break
    
    if kx792:
        print("Found KX 792 flight!")
        print("\nUser's example showed this flight WITHOUT aircraft_details:")
        print("  \"aircraft_details\": null")
        
        print("\nNow the same flight shows:")
        flight_dict = {
            "is_best": kx792.is_best,
            "name": kx792.name,
            "departure": kx792.departure,
            "arrival": kx792.arrival,
            "arrival_time_ahead": kx792.arrival_time_ahead,
            "duration": kx792.duration,
            "stops": kx792.stops,
            "delay": kx792.delay,
            "price": kx792.price,
            "flight_number": kx792.flight_number,
            "departure_airport": kx792.departure_airport,
            "arrival_airport": kx792.arrival_airport,
            "connections": kx792.connections,
            "emissions": kx792.emissions,
            "operated_by": kx792.operated_by,
            "aircraft_details": kx792.aircraft_details
        }
        
        print(json.dumps(flight_dict, indent=2))
        
        if kx792.aircraft_details:
            print(f"\n✅ SUCCESS: Flight KX 792 now has aircraft_details: {kx792.aircraft_details}")
        else:
            print("\n❌ ISSUE: Flight KX 792 still missing aircraft_details")
    else:
        print("Could not find flight KX 792 in the results")
        print("\nAvailable flights:")
        for i, flight in enumerate(result.flights[:10], 1):
            print(f"  {i}. {flight.flight_number} - {flight.name}")

if __name__ == "__main__":
    main()