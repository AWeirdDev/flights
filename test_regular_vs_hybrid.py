#!/usr/bin/env python3
"""
Test script to compare regular HTML parser vs hybrid approach
to see if the missing fields are present in regular HTML structure
"""

import os
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

def analyze_fields(flights, parser_type):
    """Analyze field availability in flight results"""
    total_flights = len(flights)
    
    field_counts = {
        'delay': 0,
        'operated_by': 0,
        'terminal_info': 0,
        'alliance': 0,
        'on_time_performance': 0
    }
    
    for flight in flights:
        if flight.delay is not None:
            field_counts['delay'] += 1
        if flight.operated_by is not None:
            field_counts['operated_by'] += 1
        if flight.terminal_info is not None:
            field_counts['terminal_info'] += 1
        if flight.alliance is not None:
            field_counts['alliance'] += 1
        if flight.on_time_performance is not None:
            field_counts['on_time_performance'] += 1
    
    print(f"\n{parser_type} Results:")
    print(f"  Total flights: {total_flights}")
    for field, count in field_counts.items():
        percentage = (count / total_flights) * 100 if total_flights > 0 else 0
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {field}: {count}/{total_flights} ({percentage:.1f}%)")
    
    return field_counts

def test_parsers():
    """Test different parser approaches"""
    print("Comparing Regular HTML Parser vs Hybrid Approach")
    print("=" * 60)
    
    # Use a route that might have more advanced fields
    filter = create_filter(
        flight_data=[FlightData(date="2025-08-15", from_airport="DFW", to_airport="ORD")],
        trip="one-way",
        passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
        seat="economy",
        max_stops=None,
    )
    
    try:
        # Test regular HTML parser with common mode (not Bright Data)
        print("Testing regular HTML parser...")
        regular_result = get_flights_from_filter(filter, mode="common", data_source='html')
        regular_counts = analyze_fields(regular_result.flights, "Regular HTML Parser")
        
        # Test hybrid approach with Bright Data
        print("\nTesting hybrid approach with Bright Data...")
        hybrid_result = get_flights_from_filter(filter, mode="bright-data", data_source='hybrid')
        hybrid_counts = analyze_fields(hybrid_result.flights, "Hybrid Approach (Bright Data)")
        
        # Compare results
        print(f"\n{'='*60}")
        print("COMPARISON")
        print(f"{'='*60}")
        
        for field in ['delay', 'operated_by', 'terminal_info', 'alliance', 'on_time_performance']:
            regular_count = regular_counts[field]
            hybrid_count = hybrid_counts[field]
            
            if regular_count > 0 and hybrid_count == 0:
                print(f"❌ {field}: Regular parser finds it ({regular_count}), hybrid doesn't")
            elif regular_count == 0 and hybrid_count > 0:
                print(f"✅ {field}: Hybrid finds it ({hybrid_count}), regular doesn't")
            elif regular_count > 0 and hybrid_count > 0:
                print(f"✅ {field}: Both find it (regular: {regular_count}, hybrid: {hybrid_count})")
            else:
                print(f"❌ {field}: Neither finds it")
        
        print(f"\nConclusion:")
        fields_only_in_regular = [field for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance'] 
                                 if regular_counts[field] > 0 and hybrid_counts[field] == 0]
        
        if fields_only_in_regular:
            print(f"Fields only found in regular HTML parser: {', '.join(fields_only_in_regular)}")
            print("This suggests the Bright Data HTML structure is missing these fields")
        else:
            print("Both parsers find the same fields - the issue is not with Bright Data HTML structure")
        
    except Exception as e:
        print(f"Error testing parsers: {e}")

if __name__ == "__main__":
    test_parsers()