#!/usr/bin/env python3

from fast_flights import FlightData, Passengers, get_flights

def test_multiple_flights():
    """Test flight number extraction for multiple flights"""
    try:
        print("Testing flight number extraction for multiple flights...")
        print("Searching for flights from NYC to LAX on 2025-08-01...")
        
        result = get_flights(
            flight_data=[
                FlightData(
                    date="2025-08-01",
                    from_airport="NYC",
                    to_airport="LAX"
                )
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            fetch_mode="common",
        )
        
        print(f"✅ Search successful!")
        print(f"Current price level: {result.current_price}")
        print(f"Found {len(result.flights)} flights")
        
        # Show first 5 flights with their flight numbers
        print("\nFirst 5 flights with flight numbers:")
        for i, flight in enumerate(result.flights[:10]):
            print(f"Flight {i+1}:")
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
            print()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_multiple_flights() 