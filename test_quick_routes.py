#!/usr/bin/env python3
"""
Quick test script to check field extraction on 2-3 routes
"""

import os
import json
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

# Test just a few routes for quick assessment
test_routes = [
    {
        "name": "JFK→LAX (Domestic US)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="LAX")],
    },
    {
        "name": "LHR→CDG (European)",
        "route": [FlightData(date="2025-08-15", from_airport="LHR", to_airport="CDG")],
    },
    {
        "name": "GCM→LHR (Baseline)",
        "route": [FlightData(date="2025-08-06", from_airport="GCM", to_airport="LHR")],
    }
]

def analyze_fields(flights, route_name):
    """Analyze field availability in flight results"""
    total_flights = len(flights)
    
    field_counts = {
        'delay': 0,
        'operated_by': 0,
        'terminal_info': 0,
        'alliance': 0,
        'on_time_performance': 0
    }
    
    field_samples = {
        'delay': [],
        'operated_by': [],
        'terminal_info': [],
        'alliance': [],
        'on_time_performance': []
    }
    
    for flight in flights:
        # Count non-null fields and collect samples
        if flight.delay is not None:
            field_counts['delay'] += 1
            if len(field_samples['delay']) < 2:
                field_samples['delay'].append(flight.delay)
        
        if flight.operated_by is not None:
            field_counts['operated_by'] += 1
            if len(field_samples['operated_by']) < 2:
                field_samples['operated_by'].append(flight.operated_by)
        
        if flight.terminal_info is not None:
            field_counts['terminal_info'] += 1
            if len(field_samples['terminal_info']) < 2:
                field_samples['terminal_info'].append(flight.terminal_info)
        
        if flight.alliance is not None:
            field_counts['alliance'] += 1
            if len(field_samples['alliance']) < 2:
                field_samples['alliance'].append(flight.alliance)
        
        if flight.on_time_performance is not None:
            field_counts['on_time_performance'] += 1
            if len(field_samples['on_time_performance']) < 2:
                field_samples['on_time_performance'].append(flight.on_time_performance)
    
    return field_counts, field_samples, total_flights

def test_route(route_info):
    """Test a specific route"""
    print(f"\n{'='*50}")
    print(f"Testing: {route_info['name']}")
    print(f"{'='*50}")
    
    try:
        # Create filter
        filter = create_filter(
            flight_data=route_info['route'],
            trip="one-way",
            passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
            seat="economy",
            max_stops=None,
        )
        
        # Get flights using Bright Data with hybrid data source
        print("Fetching flights...")
        result = get_flights_from_filter(filter, mode="bright-data")
        
        if not result or not result.flights:
            print("❌ No flights found")
            return None
        
        # Analyze field availability
        field_counts, field_samples, total_flights = analyze_fields(result.flights, route_info['name'])
        
        print(f"✅ Found {total_flights} flights")
        
        # Display field statistics
        print(f"\nField Availability:")
        for field, count in field_counts.items():
            percentage = (count / total_flights) * 100 if total_flights > 0 else 0
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {field}: {count}/{total_flights} ({percentage:.1f}%)")
            
            # Show samples if available
            if field_samples[field]:
                print(f"      Samples: {field_samples[field]}")
        
        return field_counts
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return None

def main():
    """Main test function"""
    print("Quick Field Extraction Test")
    print("=" * 50)
    print("Testing: delay, operated_by, terminal_info, alliance, on_time_performance")
    
    results = []
    
    for route_info in test_routes:
        result = test_route(route_info)
        if result:
            results.append((route_info['name'], result))
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    
    # Check which fields are never found
    never_found = []
    for field in ['delay', 'operated_by', 'terminal_info', 'alliance', 'on_time_performance']:
        total_count = sum(result[1].get(field, 0) for result in results)
        if total_count == 0:
            never_found.append(field)
    
    if never_found:
        print(f"❌ Fields NEVER found (need debugging): {', '.join(never_found)}")
    else:
        print("✅ All fields found in at least one route")
    
    print(f"\nField extraction working for: {5 - len(never_found)}/5 fields")

if __name__ == "__main__":
    main()