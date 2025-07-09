#!/usr/bin/env python3

from fast_flights import FlightData, Passengers, create_filter

def test_filter_generation():
    """Test that we can generate protobuf filters correctly"""
    try:
        print("Testing filter generation...")
        
        # Create flight data
        flight_data = [
            FlightData(
                date="2025-01-15",
                from_airport="JFK",
                to_airport="LAX"
            )
        ]
        
        # Create passengers
        passengers = Passengers(adults=1)
        
        # Create filter
        filter_obj = create_filter(
            flight_data=flight_data,
            trip="one-way",
            passengers=passengers,
            seat="economy"
        )
        
        # Generate base64 encoded filter
        b64_filter = filter_obj.as_b64().decode('utf-8')
        
        print(f"✅ Filter generation successful!")
        print(f"Generated filter: {b64_filter}")
        
        # Test URL generation
        url = f"https://www.google.com/travel/flights?tfs={b64_filter}&hl=en"
        print(f"Generated URL: {url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Filter generation failed: {e}")
        return False

if __name__ == "__main__":
    test_filter_generation() 