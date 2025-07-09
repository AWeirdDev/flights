#!/usr/bin/env python3
"""
Test edge cases to find the missing fields:
- Very recent dates (higher chance of delays)
- Known problematic airports/routes
- Specific airline alliances
- Different times of day
"""

import os
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

# Get tomorrow's date and next few days for more realistic delay data
tomorrow = datetime.now() + timedelta(days=1)
next_week = datetime.now() + timedelta(days=7)

# Edge case routes targeting specific scenarios
edge_case_routes = [
    # Very recent dates (higher chance of real delays)
    {
        "name": "LGA→ORD (Tomorrow - High Delay Route)",
        "route": [FlightData(date=tomorrow.strftime("%Y-%m-%d"), from_airport="LGA", to_airport="ORD")],
        "target_fields": ["delay", "on_time_performance"],
        "category": "recent_date"
    },
    {
        "name": "EWR→LAX (Tomorrow - Busy Route)",
        "route": [FlightData(date=tomorrow.strftime("%Y-%m-%d"), from_airport="EWR", to_airport="LAX")],
        "target_fields": ["delay", "on_time_performance"],
        "category": "recent_date"
    },
    {
        "name": "JFK→MIA (Next Week - Hurricane Season)",
        "route": [FlightData(date=next_week.strftime("%Y-%m-%d"), from_airport="JFK", to_airport="MIA")],
        "target_fields": ["delay", "on_time_performance"],
        "category": "recent_date"
    },
    
    # Known alliance airlines and routes
    {
        "name": "SFO→FRA (Lufthansa - Star Alliance)",
        "route": [FlightData(date="2025-08-15", from_airport="SFO", to_airport="FRA")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "star_alliance_specific"
    },
    {
        "name": "JFK→LHR (British Airways - oneworld)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="LHR")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "oneworld_specific"
    },
    {
        "name": "JFK→CDG (Air France - SkyTeam)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="CDG")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "skyteam_specific"
    },
    
    # Large hub airports with multiple terminals
    {
        "name": "JFK→LAX (Multiple Terminal Airports)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="LAX")],
        "target_fields": ["terminal_info"],
        "category": "multi_terminal"
    },
    {
        "name": "ORD→DFW (Major Hub to Hub)",
        "route": [FlightData(date="2025-08-15", from_airport="ORD", to_airport="DFW")],
        "target_fields": ["terminal_info"],
        "category": "multi_terminal"
    },
    {
        "name": "LHR→FRA (European Major Hubs)",
        "route": [FlightData(date="2025-08-15", from_airport="LHR", to_airport="FRA")],
        "target_fields": ["terminal_info", "alliance"],
        "category": "multi_terminal"
    },
    
    # Peak travel times (Monday morning, Friday evening)
    {
        "name": "DCA→LGA (Monday AM - Peak Business)",
        "route": [FlightData(date="2025-08-18", from_airport="DCA", to_airport="LGA")],  # Monday
        "target_fields": ["delay", "on_time_performance"],
        "category": "peak_time"
    },
    {
        "name": "LAX→SFO (Friday PM - Peak Travel)",
        "route": [FlightData(date="2025-08-22", from_airport="LAX", to_airport="SFO")],  # Friday
        "target_fields": ["delay", "on_time_performance"],
        "category": "peak_time"
    },
    
    # International long-haul (more likely to have detailed info)
    {
        "name": "JFK→NRT (Trans-Pacific Long-haul)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="NRT")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "long_haul"
    },
    {
        "name": "LAX→LHR (Trans-Atlantic Long-haul)",
        "route": [FlightData(date="2025-08-15", from_airport="LAX", to_airport="LHR")],
        "target_fields": ["alliance", "terminal_info"],
        "category": "long_haul"
    },
    
    # Known delay-prone routes and airports
    {
        "name": "LGA→BOS (Delay-prone Northeast)",
        "route": [FlightData(date="2025-08-15", from_airport="LGA", to_airport="BOS")],
        "target_fields": ["delay", "on_time_performance"],
        "category": "delay_prone"
    },
    {
        "name": "ORD→MSP (Weather-sensitive Midwest)",
        "route": [FlightData(date="2025-08-15", from_airport="ORD", to_airport="MSP")],
        "target_fields": ["delay", "on_time_performance"],
        "category": "delay_prone"
    }
]

def analyze_fields(flights, route_name):
    """Analyze field availability in flight results with detailed output"""
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
    """Test a specific route with detailed error handling"""
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
    print("Edge Case Field Discovery Test")
    print("=" * 70)
    print("Testing edge cases to find delay, terminal_info, alliance, on_time_performance")
    print(f"Using dates: {tomorrow.strftime('%Y-%m-%d')} (tomorrow) and {next_week.strftime('%Y-%m-%d')} (next week)")
    
    # Execute all routes in parallel
    print(f"\nTesting {len(edge_case_routes)} edge case routes...")
    results = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        # Submit all tasks
        future_to_route = {executor.submit(test_route, route_info): route_info for route_info in edge_case_routes}
        
        # Collect results as they complete
        for future in as_completed(future_to_route):
            route_info = future_to_route[future]
            try:
                result = future.result()
                results.append(result)
                status = "✅" if result['success'] else "❌"
                print(f"{status} {result['name']}")
            except Exception as exc:
                print(f"❌ {route_info['name']} - {exc}")
    
    # Analyze results
    print(f"\n{'='*70}")
    print("EDGE CASE DISCOVERIES")
    print(f"{'='*70}")
    
    # Track any discoveries
    discoveries = {
        'delay': [],
        'terminal_info': [],
        'alliance': [],
        'on_time_performance': []
    }
    
    successful_tests = 0
    total_flights_tested = 0
    
    for result in results:
        if result['success']:
            successful_tests += 1
            total_flights_tested += result['total_flights']
            
            # Look for any discoveries
            for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance']:
                if result['field_counts'][field] > 0:
                    discoveries[field].append({
                        'route': result['name'],
                        'category': result['category'],
                        'count': result['field_counts'][field],
                        'total': result['total_flights'],
                        'samples': result['field_samples'][field]
                    })
    
    # Report findings
    any_discoveries = False
    for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance']:
        if discoveries[field]:
            any_discoveries = True
            print(f"\n🎉 {field.upper()} FOUND!")
            for disc in discoveries[field]:
                percentage = (disc['count'] / disc['total']) * 100
                print(f"  ✅ {disc['route']} ({disc['category']}): {disc['count']}/{disc['total']} ({percentage:.1f}%)")
                if disc['samples']:
                    print(f"     Examples: {disc['samples']}")
        else:
            print(f"\n❌ {field.upper()}: Still not found")
    
    # Summary
    print(f"\n{'='*70}")
    print("EDGE CASE SUMMARY")
    print(f"{'='*70}")
    print(f"Routes tested: {successful_tests}/{len(edge_case_routes)}")
    print(f"Total flights analyzed: {total_flights_tested}")
    
    if any_discoveries:
        found_fields = [field for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance'] if discoveries[field]]
        print(f"\n🎉 BREAKTHROUGH: Found {len(found_fields)} field(s): {', '.join(found_fields)}")
    else:
        print(f"\n❌ STILL NO DISCOVERIES: These fields may not be available in Google Flights API responses")
        print("Possible reasons:")
        print("  - Fields only available in web interface, not API")
        print("  - Fields only available for specific airlines/routes not tested")
        print("  - Fields only available during actual operational disruptions")
        print("  - Fields deprecated or moved to different data structure")

if __name__ == "__main__":
    main()