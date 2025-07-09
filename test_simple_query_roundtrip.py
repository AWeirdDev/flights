#!/usr/bin/env python3

from fast_flights import FlightData, Passengers, get_flights

def test_simple_query_roundtrip():
    """Test the simple query approach with round-trip flights"""
    try:
        print("Testing round-trip flights with protobuf approach...")
        print("Searching for round-trip flights JFK-LAX-JFK on 2025-08-01 and 2025-08-10...")
        
        result = get_flights(
            flight_data=[
                FlightData(
                    date="2025-08-01",
                    from_airport="JFK",
                    to_airport="LAX"
                ),
                FlightData(
                    date="2025-08-10",
                    from_airport="LAX",
                    to_airport="JFK"
                )
            ],
            trip="round-trip",
            seat="economy",
            passengers=Passengers(adults=1),
            fetch_mode="common",
        )
        
        print(f"✅ Round-trip search successful!")
        
        # Handle different result types
        if result is None:
            print("No results found")
        elif hasattr(result, 'current_price') and result.current_price:
            # HTML parsing result
            print(f"Current price level: {result.current_price}")
            if hasattr(result, 'flights') and result.flights:
                print(f"Found {len(result.flights)} flights")
                
                print("\nFirst 3 flights details:")
                for i, flight in enumerate(result.flights[:3]):
                    print(f"\nFlight {i+1}:")
                    print(f"  Airline: {flight.name}")
                    print(f"  Flight number: {flight.flight_number}")
                    print(f"  Departure: {flight.departure}")
                    print(f"  Departure airport: {flight.departure_airport}")
                    print(f"  Arrival: {flight.arrival}")
                    print(f"  Arrival airport: {flight.arrival_airport}")
                    print(f"  Duration: {flight.duration}")
                    print(f"  Stops: {flight.stops}")
                    print(f"  Price: {flight.price}")
                    print(f"  Best flight: {flight.is_best}")
            else:
                print("No flights found in result")
        else:
            print("Unexpected result format")
            
    except Exception as e:
        print(f"❌ Round-trip test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_query_roundtrip() 