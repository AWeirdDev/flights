#!/usr/bin/env python3

from fast_flights import FlightData, Passengers, get_flights

def test_simple_query():
    """Test the new simple query approach"""
    try:
        print("Testing simple query approach...")
        print("Searching for flights from JFK to LAX on 2025-08-01...")
        
        result = get_flights(
            flight_data=[
                FlightData(
                    date="2025-08-01",
                    from_airport="JFK",
                    to_airport="LAX"
                )
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            fetch_mode="common",
            use_simple_query=True,  # Use the new simple query approach
        )
        
        print(f"✅ Simple query search successful!")
        
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
                    print(f"  Connecting airports: {flight.connecting_airports}")
                    print(f"  Duration: {flight.duration}")
                    print(f"  Stops: {flight.stops}")
                    print(f"  Price: {flight.price}")
                    print(f"  Best flight: {flight.is_best}")
            else:
                print("No flights found in result")
        else:
            print("Unexpected result format")
            
    except Exception as e:
        print(f"❌ Simple query test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_query() 