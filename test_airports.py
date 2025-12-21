#!/usr/bin/env python3

from fast_flights import Airport, search_airport

def test_airport_functionality():
    """Test airport enum and search functionality"""
    try:
        print("Testing airport functionality...")
        
        # Test direct airport access
        print(f"JFK airport: {Airport.JOHN_F_KENNEDY_INTERNATIONAL_AIRPORT.value}")
        print(f"LAX airport: {Airport.LOS_ANGELES_INTERNATIONAL_AIRPORT.value}")
        print(f"TPE airport: {Airport.TAIWAN_TAOYUAN_INTERNATIONAL_AIRPORT.value}")
        
        # Test airport search by name
        print("\nSearching for airports containing 'New York':")
        ny_results = search_airport("New York")
        for airport in ny_results[:3]:  # Show first 3 results
            print(f"  {airport.name}: {airport.value}")
        
        print("\nSearching for airports containing 'Los Angeles':")
        la_results = search_airport("Los Angeles")
        for airport in la_results[:3]:  # Show first 3 results
            print(f"  {airport.name}: {airport.value}")
        
        print("\nSearching for airports containing 'Taipei':")
        taipei_results = search_airport("Taipei")
        for airport in taipei_results[:3]:  # Show first 3 results
            print(f"  {airport.name}: {airport.value}")
        
        print(f"\n✅ Airport functionality test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Airport functionality test failed: {e}")
        return False

if __name__ == "__main__":
    test_airport_functionality() 