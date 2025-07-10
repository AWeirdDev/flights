#!/usr/bin/env python3
"""
Test script to check field extraction across multiple routes using Bright Data API
Tests: delay, operated_by, terminal_info, alliance, on_time_performance
"""

import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

# Test routes - variety of domestic and international routes
test_routes = [
    {
        "name": "JFK→LAX (Domestic US)",
        "route": [
            FlightData(date="2025-08-15", from_airport="JFK", to_airport="LAX"),
        ],
        "expected_fields": ["delay", "operated_by", "alliance"]
    },
    {
        "name": "LHR→CDG (European)",
        "route": [
            FlightData(date="2025-08-15", from_airport="LHR", to_airport="CDG"),
        ],
        "expected_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "SFO→NRT (International)",
        "route": [
            FlightData(date="2025-08-15", from_airport="SFO", to_airport="NRT"),
        ],
        "expected_fields": ["terminal_info", "alliance", "operated_by"]
    },
    {
        "name": "DFW→ORD (Hub-to-Hub)",
        "route": [
            FlightData(date="2025-08-15", from_airport="DFW", to_airport="ORD"),
        ],
        "expected_fields": ["operated_by", "alliance", "delay"]
    },
    {
        "name": "ATL→JFK (Delta Hub)",
        "route": [
            FlightData(date="2025-08-15", from_airport="ATL", to_airport="JFK"),
        ],
        "expected_fields": ["alliance", "delay", "on_time_performance"]
    },
    {
        "name": "LGA→DCA (Short Domestic)",
        "route": [
            FlightData(date="2025-08-15", from_airport="LGA", to_airport="DCA"),
        ],
        "expected_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "GCM→LHR (Baseline)",
        "route": [
            FlightData(date="2025-08-06", from_airport="GCM", to_airport="LHR"),
        ],
        "expected_fields": ["alliance", "operated_by"]
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
        # Count non-null fields
        if flight.delay is not None:
            field_counts['delay'] += 1
            if len(field_samples['delay']) < 3:
                field_samples['delay'].append(flight.delay)
        
        if flight.operated_by is not None:
            field_counts['operated_by'] += 1
            if len(field_samples['operated_by']) < 3:
                field_samples['operated_by'].append(flight.operated_by)
        
        if flight.terminal_info is not None:
            field_counts['terminal_info'] += 1
            if len(field_samples['terminal_info']) < 3:
                field_samples['terminal_info'].append(flight.terminal_info)
        
        if flight.alliance is not None:
            field_counts['alliance'] += 1
            if len(field_samples['alliance']) < 3:
                field_samples['alliance'].append(flight.alliance)
        
        if flight.on_time_performance is not None:
            field_counts['on_time_performance'] += 1
            if len(field_samples['on_time_performance']) < 3:
                field_samples['on_time_performance'].append(flight.on_time_performance)
    
    return field_counts, field_samples, total_flights

def test_route(route_info):
    """Test a specific route"""
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
        result = get_flights_from_filter(filter, mode="bright-data")
        
        if not result or not result.flights:
            return {
                'name': route_info['name'],
                'success': False,
                'error': 'No flights found',
                'field_counts': None,
                'field_samples': None,
                'total_flights': 0
            }
        
        # Analyze field availability
        field_counts, field_samples, total_flights = analyze_fields(result.flights, route_info['name'])
        
        return {
            'name': route_info['name'],
            'success': True,
            'error': None,
            'field_counts': field_counts,
            'field_samples': field_samples,
            'total_flights': total_flights,
            'expected_fields': route_info['expected_fields'],
            'current_price': result.current_price
        }
        
    except Exception as e:
        return {
            'name': route_info['name'],
            'success': False,
            'error': f"{type(e).__name__}: {e}",
            'field_counts': None,
            'field_samples': None,
            'total_flights': 0
        }

def main():
    """Main test function"""
    print("Testing Field Extraction Across Multiple Routes")
    print("=" * 60)
    print("Testing fields: delay, operated_by, terminal_info, alliance, on_time_performance")
    print("Using Bright Data API with hybrid data source (parallel execution)")
    
    # Execute all routes in parallel
    print(f"\nTesting {len(test_routes)} routes in parallel...")
    results = []
    
    with ThreadPoolExecutor(max_workers=len(test_routes)) as executor:
        # Submit all tasks
        future_to_route = {executor.submit(test_route, route_info): route_info for route_info in test_routes}
        
        # Collect results as they complete
        for future in as_completed(future_to_route):
            route_info = future_to_route[future]
            try:
                result = future.result()
                results.append(result)
                print(f"✅ Completed: {result['name']}")
            except Exception as exc:
                print(f"❌ Failed: {route_info['name']} - {exc}")
                results.append({
                    'name': route_info['name'],
                    'success': False,
                    'error': str(exc),
                    'field_counts': None,
                    'field_samples': None,
                    'total_flights': 0
                })
    
    # Process results
    print(f"\n{'='*60}")
    print("DETAILED RESULTS")
    print(f"{'='*60}")
    
    overall_stats = {
        'delay': {'total': 0, 'routes_with_data': 0},
        'operated_by': {'total': 0, 'routes_with_data': 0},
        'terminal_info': {'total': 0, 'routes_with_data': 0},
        'alliance': {'total': 0, 'routes_with_data': 0},
        'on_time_performance': {'total': 0, 'routes_with_data': 0}
    }
    
    successful_tests = 0
    total_flights_tested = 0
    
    # Display individual route results
    for result in results:
        print(f"\n{result['name']}:")
        if result['success']:
            successful_tests += 1
            total_flights_tested += result['total_flights']
            
            print(f"  ✅ Found {result['total_flights']} flights")
            print(f"  Current price: {result['current_price']}")
            
            # Display field statistics
            print(f"  Field Availability:")
            for field, count in result['field_counts'].items():
                percentage = (count / result['total_flights']) * 100 if result['total_flights'] > 0 else 0
                print(f"    {field}: {count}/{result['total_flights']} ({percentage:.1f}%)")
                
                # Show samples if available
                if result['field_samples'][field]:
                    print(f"      Samples: {result['field_samples'][field][:3]}")
            
            # Check expected fields
            print(f"  Expected Fields Analysis:")
            for expected_field in result['expected_fields']:
                count = result['field_counts'].get(expected_field, 0)
                if count > 0:
                    print(f"    ✅ {expected_field}: Found in {count} flights")
                else:
                    print(f"    ❌ {expected_field}: Not found")
            
            # Update overall stats
            for field, count in result['field_counts'].items():
                overall_stats[field]['total'] += count
                if count > 0:
                    overall_stats[field]['routes_with_data'] += 1
        else:
            print(f"  ❌ Failed: {result['error']}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY REPORT")
    print(f"{'='*60}")
    print(f"Routes tested: {successful_tests}/{len(test_routes)}")
    print(f"Total flights analyzed: {total_flights_tested}")
    
    print(f"\nOverall Field Statistics:")
    for field, stats in overall_stats.items():
        total_occurrences = stats['total']
        routes_with_data = stats['routes_with_data']
        percentage = (total_occurrences / total_flights_tested) * 100 if total_flights_tested > 0 else 0
        
        print(f"  {field}:")
        print(f"    Total occurrences: {total_occurrences}/{total_flights_tested} ({percentage:.1f}%)")
        print(f"    Routes with data: {routes_with_data}/{successful_tests}")
        
        if total_occurrences == 0:
            print(f"    Status: ❌ NEVER FOUND - Check extraction logic")
        elif routes_with_data == 1:
            print(f"    Status: ⚠️  RARE - Found in only 1 route")
        elif routes_with_data < successful_tests // 2:
            print(f"    Status: ⚠️  UNCOMMON - Found in {routes_with_data} routes")
        else:
            print(f"    Status: ✅ COMMON - Found in {routes_with_data} routes")
    
    print(f"\nNext Steps:")
    for field, stats in overall_stats.items():
        if stats['total'] == 0:
            print(f"  - Debug {field} extraction logic - never found")
        elif stats['routes_with_data'] <= 1:
            print(f"  - Investigate {field} extraction - very rare")

if __name__ == "__main__":
    main()