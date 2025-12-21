#!/usr/bin/env python3

from fast_flights import FlightData, Passengers, get_flights

def test_simple_search():
    """Test with a simple one-way flight search"""
    try:
        print("Testing fast-flights library...")
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
        )
        
        print(f"✅ Search successful!")
        
        # Handle different result types
        if result is None:
            print("No results found")
        elif hasattr(result, 'current_price') and result.current_price:
            # HTML parsing result
            print(f"Current price level: {result.current_price}")
            if hasattr(result, 'flights') and result.flights:
                print(f"Found {len(result.flights)} flights")
                
                print("\nFirst flight details:")
                flight = result.flights[0]
                print(f"  Airline: {flight.name}")
                print(f"  Flight number: {flight.flight_number}")
                print(f"  Departure: {flight.departure}")
                print(f"  Arrival: {flight.arrival}")
                print(f"  Duration: {flight.duration}")
                print(f"  Stops: {flight.stops}")
                print(f"  Price: {flight.price}")
                print(f"  Best flight: {flight.is_best}")
            else:
                print("No flights found in result")
        elif hasattr(result, 'best') and result.best:
            # Decoded protobuf result
            print(f"Found {len(result.best)} best flights")
            if hasattr(result, 'other'):
                print(f"Found {len(result.other)} other flights")
            
            print("\nFirst best flight details:")
            itinerary = result.best[0]
            print(f"  Airline: {itinerary.airline_code}")
            print(f"  Departure: {itinerary.departure_airport}")
            print(f"  Arrival: {itinerary.arrival_airport}")
            print(f"  Travel time: {itinerary.travel_time} minutes")
        else:
            print(f"Unexpected result type: {type(result)}")
            print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_simple_search() 