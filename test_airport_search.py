#!/usr/bin/env python3
"""
Test file for enhanced airport search functionality in fast-flights
Uses Owen Roberts International Airport (GCM) in Cayman Islands as the main example
"""

from fast_flights import search_airport

def print_results(query, results, max_display=5):
    """Helper function to print search results"""
    print(f"\nSearch for '{query}': {len(results)} result(s)")
    for i, airport in enumerate(results[:max_display]):
        print(f"  {i+1}. {airport}")
    if len(results) > max_display:
        print(f"  ... and {len(results) - max_display} more")

def main():
    print("Testing enhanced airport search functionality")
    print("=" * 80)
    print("Main example: Owen Roberts International Airport (GCM) in George Town, Cayman Islands")
    print("=" * 80)
    
    # Test 1: Search by airport code (case-sensitive)
    print("\n1. SEARCH BY AIRPORT CODE (case-sensitive)")
    print("-" * 40)
    results = search_airport("GCM")
    print_results("GCM", results)
    
    # Test case sensitivity - should not match
    results = search_airport("gcm")
    print_results("gcm", results)
    
    # Test 2: Search by ICAO code (case-sensitive)
    print("\n\n2. SEARCH BY ICAO CODE (case-sensitive)")
    print("-" * 40)
    results = search_airport("MWCR")
    print_results("MWCR", results)
    
    # Test case sensitivity - should not match
    results = search_airport("mwcr")
    print_results("mwcr", results)
    
    # Test 3: Search by country code (case-sensitive)
    print("\n\n3. SEARCH BY COUNTRY CODE (case-sensitive)")
    print("-" * 40)
    results = search_airport("KY")
    print_results("KY", results)
    print("\nNote: KY is the country code for Cayman Islands (3 airports)")
    print("Additional results come from airports with 'KY' in their enum names (e.g., KYIV, KYZYL)")
    
    # Test case sensitivity - should not match country code but might match in enum names
    results = search_airport("ky")
    print_results("ky", results)
    print("Note: Lowercase 'ky' doesn't match country code but matches enum names")
    
    # Test 4: Search by city name (case-insensitive)
    print("\n\n4. SEARCH BY CITY NAME (case-insensitive)")
    print("-" * 40)
    results = search_airport("George Town")
    print_results("George Town", results)
    print("\nNote: George Town exists in multiple countries (Cayman Islands, Bahamas, etc.)")
    
    # Test case insensitivity
    results = search_airport("george town")
    print_results("george town", results)
    
    # Test partial match
    results = search_airport("george")
    print_results("george", results, max_display=10)
    
    # Test 5: Search by enum member name (case-insensitive)
    print("\n\n5. SEARCH BY ENUM MEMBER NAME (case-insensitive)")
    print("-" * 40)
    results = search_airport("owen roberts")
    print_results("owen roberts", results)
    
    results = search_airport("OWEN ROBERTS")
    print_results("OWEN ROBERTS", results)
    
    results = search_airport("owen_roberts")
    print_results("owen_roberts", results)
    
    # Test 6: Edge cases
    print("\n\n6. EDGE CASES")
    print("-" * 40)
    
    # Non-existent search
    results = search_airport("ZZZZZ")
    print_results("ZZZZZ", results)
    
    # Very common word that might match many airports
    results = search_airport("international")
    print(f"\nSearch for 'international': {len(results)} result(s)")
    print("(Too many to display - this matches all airports with 'International' in their name)")
    
    # Empty string
    results = search_airport("")
    print(f"\nSearch for '' (empty string): {len(results)} result(s)")
    
    # Test 7: Other Cayman Islands airports
    print("\n\n7. OTHER CAYMAN ISLANDS AIRPORTS")
    print("-" * 40)
    print("Getting actual Cayman Islands airports only (not just 'KY' matches)...")
    
    # Import to access the data directly
    from fast_flights.airport_data import get_airport_data
    airport_data = get_airport_data()
    cayman_airports = airport_data.by_country.get("KY", [])
    
    print(f"\nFound {len(cayman_airports)} airport(s) in Cayman Islands:")
    for i, airport_info in enumerate(cayman_airports, 1):
        print(f"  {i}. {airport_info.enum_member}")
        print(f"     - {airport_info.name} ({airport_info.code})")
        if airport_info.icao:
            print(f"     - ICAO: {airport_info.icao}")
        if airport_info.city:
            print(f"     - City: {airport_info.city}")
    
    print("\n" + "=" * 80)
    print("Test completed successfully!")

if __name__ == "__main__":
    main()