#!/usr/bin/env python3
"""
Comprehensive test script to find routes with delay, terminal_info, alliance, on_time_performance
Tests 20 diverse routes in parallel to maximize chances of finding these fields
"""

import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

# Comprehensive test routes - 20 diverse routes targeting different field types
test_routes = [
    # Weather-prone routes (likely delay)
    {
        "name": "ORD→LGA (Weather-prone)",
        "route": [FlightData(date="2025-01-15", from_airport="ORD", to_airport="LGA")],
        "target_fields": ["delay"],
        "category": "weather_prone"
    },
    {
        "name": "BOS→DCA (Northeast Winter)",
        "route": [FlightData(date="2025-01-20", from_airport="BOS", to_airport="DCA")],
        "target_fields": ["delay"],
        "category": "weather_prone"
    },
    {
        "name": "EWR→ORD (Busy Route)",
        "route": [FlightData(date="2025-08-18", from_airport="EWR", to_airport="ORD")],
        "target_fields": ["delay"],
        "category": "weather_prone"
    },
    {
        "name": "MIA→JFK (Hurricane Season)",
        "route": [FlightData(date="2025-09-15", from_airport="MIA", to_airport="JFK")],
        "target_fields": ["delay"],
        "category": "weather_prone"
    },
    
    # Major international hubs (likely terminal_info)
    {
        "name": "JFK→LHR (Major Hubs)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="LHR")],
        "target_fields": ["terminal_info", "alliance"],
        "category": "international_hub"
    },
    {
        "name": "LAX→NRT (Trans-Pacific)",
        "route": [FlightData(date="2025-08-20", from_airport="LAX", to_airport="NRT")],
        "target_fields": ["terminal_info", "alliance"],
        "category": "international_hub"
    },
    {
        "name": "ORD→FRA (Trans-Atlantic)",
        "route": [FlightData(date="2025-08-25", from_airport="ORD", to_airport="FRA")],
        "target_fields": ["terminal_info", "alliance"],
        "category": "international_hub"
    },
    {
        "name": "LHR→CDG (European Hubs)",
        "route": [FlightData(date="2025-08-15", from_airport="LHR", to_airport="CDG")],
        "target_fields": ["terminal_info", "alliance"],
        "category": "international_hub"
    },
    {
        "name": "FRA→AMS (European Network)",
        "route": [FlightData(date="2025-08-16", from_airport="FRA", to_airport="AMS")],
        "target_fields": ["terminal_info", "alliance"],
        "category": "international_hub"
    },
    
    # Star Alliance routes (likely alliance)
    {
        "name": "SFO→FRA (Star Alliance)",
        "route": [FlightData(date="2025-08-15", from_airport="SFO", to_airport="FRA")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "star_alliance"
    },
    {
        "name": "NRT→FRA (Star Alliance Asian)",
        "route": [FlightData(date="2025-08-20", from_airport="NRT", to_airport="FRA")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "star_alliance"
    },
    {
        "name": "YYZ→FRA (Star Alliance North)",
        "route": [FlightData(date="2025-08-18", from_airport="YYZ", to_airport="FRA")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "star_alliance"
    },
    
    # oneworld routes (likely alliance)
    {
        "name": "DFW→LHR (oneworld)",
        "route": [FlightData(date="2025-08-15", from_airport="DFW", to_airport="LHR")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "oneworld"
    },
    {
        "name": "LAX→LHR (oneworld Pacific)",
        "route": [FlightData(date="2025-08-20", from_airport="LAX", to_airport="LHR")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "oneworld"
    },
    
    # SkyTeam routes (likely alliance)
    {
        "name": "JFK→CDG (SkyTeam)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="CDG")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "skyteam"
    },
    {
        "name": "ATL→CDG (SkyTeam Hub)",
        "route": [FlightData(date="2025-08-18", from_airport="ATL", to_airport="CDG")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "skyteam"
    },
    
    # High-traffic business routes (likely on_time_performance)
    {
        "name": "LGA→DCA (Business Shuttle)",
        "route": [FlightData(date="2025-08-18", from_airport="LGA", to_airport="DCA")],
        "target_fields": ["on_time_performance", "delay"],
        "category": "business_shuttle"
    },
    {
        "name": "BOS→DCA (Business Corridor)",
        "route": [FlightData(date="2025-08-19", from_airport="BOS", to_airport="DCA")],
        "target_fields": ["on_time_performance", "delay"],
        "category": "business_shuttle"
    },
    {
        "name": "LAX→SFO (California Corridor)",
        "route": [FlightData(date="2025-08-15", from_airport="LAX", to_airport="SFO")],
        "target_fields": ["on_time_performance", "delay"],
        "category": "business_shuttle"
    },
    {
        "name": "JFK→BOS (Northeast Corridor)",
        "route": [FlightData(date="2025-08-20", from_airport="JFK", to_airport="BOS")],
        "target_fields": ["on_time_performance", "delay"],
        "category": "business_shuttle"
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
        result = get_flights_from_filter(filter, mode="bright-data", data_source='hybrid')
        
        if not result or not result.flights:
            return {
                'name': route_info['name'],
                'category': route_info['category'],
                'target_fields': route_info['target_fields'],
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
            'category': route_info['category'],
            'target_fields': route_info['target_fields'],
            'success': True,
            'error': None,
            'field_counts': field_counts,
            'field_samples': field_samples,
            'total_flights': total_flights,
            'current_price': result.current_price
        }
        
    except Exception as e:
        return {
            'name': route_info['name'],
            'category': route_info['category'],
            'target_fields': route_info['target_fields'],
            'success': False,
            'error': f"{type(e).__name__}: {e}",
            'field_counts': None,
            'field_samples': None,
            'total_flights': 0
        }

def main():
    """Main test function"""
    print("Comprehensive Field Discovery Test")
    print("=" * 70)
    print("Testing 20 diverse routes to find delay, terminal_info, alliance, on_time_performance")
    print("Using parallel execution with Bright Data API")
    
    # Execute all routes in parallel
    print(f"\nTesting {len(test_routes)} routes in parallel...")
    results = []
    
    with ThreadPoolExecutor(max_workers=8) as executor:  # Limit to 8 concurrent requests
        # Submit all tasks
        future_to_route = {executor.submit(test_route, route_info): route_info for route_info in test_routes}
        
        # Collect results as they complete
        for future in as_completed(future_to_route):
            route_info = future_to_route[future]
            try:
                result = future.result()
                results.append(result)
                status = "✅" if result['success'] else "❌"
                print(f"{status} Completed: {result['name']}")
            except Exception as exc:
                print(f"❌ Failed: {route_info['name']} - {exc}")
                results.append({
                    'name': route_info['name'],
                    'category': route_info['category'],
                    'target_fields': route_info['target_fields'],
                    'success': False,
                    'error': str(exc),
                    'field_counts': None,
                    'field_samples': None,
                    'total_flights': 0
                })
    
    # Process and analyze results
    print(f"\n{'='*70}")
    print("FIELD DISCOVERY RESULTS")
    print(f"{'='*70}")
    
    # Track discoveries
    discoveries = {
        'delay': [],
        'terminal_info': [],
        'alliance': [],
        'on_time_performance': []
    }
    
    successful_tests = 0
    total_flights_tested = 0
    
    # Analyze each route
    for result in results:
        if result['success']:
            successful_tests += 1
            total_flights_tested += result['total_flights']
            
            # Check for discoveries
            for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance']:
                if result['field_counts'][field] > 0:
                    discoveries[field].append({
                        'route': result['name'],
                        'category': result['category'],
                        'count': result['field_counts'][field],
                        'total': result['total_flights'],
                        'samples': result['field_samples'][field]
                    })
    
    # Report discoveries
    print(f"\n🎯 FIELD DISCOVERIES:")
    for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance']:
        if discoveries[field]:
            print(f"\n✅ {field.upper()} FOUND:")
            for disc in discoveries[field]:
                percentage = (disc['count'] / disc['total']) * 100
                print(f"  • {disc['route']} ({disc['category']}): {disc['count']}/{disc['total']} ({percentage:.1f}%)")
                if disc['samples']:
                    print(f"    Samples: {disc['samples']}")
        else:
            print(f"\n❌ {field.upper()}: Still not found")
    
    # Category analysis
    print(f"\n📊 CATEGORY ANALYSIS:")
    categories = {}
    for result in results:
        if result['success']:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'routes': 0, 'flights': 0, 'findings': {}}
            categories[cat]['routes'] += 1
            categories[cat]['flights'] += result['total_flights']
            
            for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance']:
                if result['field_counts'][field] > 0:
                    if field not in categories[cat]['findings']:
                        categories[cat]['findings'][field] = 0
                    categories[cat]['findings'][field] += result['field_counts'][field]
    
    for cat, data in categories.items():
        print(f"\n{cat.replace('_', ' ').title()}:")
        print(f"  Routes tested: {data['routes']}")
        print(f"  Total flights: {data['flights']}")
        if data['findings']:
            print(f"  Field discoveries: {data['findings']}")
        else:
            print(f"  No field discoveries")
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Routes tested: {successful_tests}/{len(test_routes)}")
    print(f"Total flights analyzed: {total_flights_tested}")
    
    found_fields = [field for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance'] if discoveries[field]]
    still_missing = [field for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance'] if not discoveries[field]]
    
    if found_fields:
        print(f"\n✅ FOUND FIELDS: {', '.join(found_fields)}")
    if still_missing:
        print(f"\n❌ STILL MISSING: {', '.join(still_missing)}")
    
    print(f"\nField extraction success rate: {len(found_fields)}/4 missing fields found")
    
    if len(found_fields) == 4:
        print("\n🎉 SUCCESS: All missing fields found! Extraction logic is working correctly.")
    elif found_fields:
        print(f"\n⚠️  PARTIAL SUCCESS: Found {len(found_fields)} out of 4 missing fields.")
        print("Consider testing more routes or different time periods for remaining fields.")
    else:
        print("\n❌ NO SUCCESS: No missing fields found. May need to test different route types or seasons.")

if __name__ == "__main__":
    main()