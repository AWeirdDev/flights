#!/usr/bin/env python3
"""
Test the hybrid parser with debug_connecting_flights2.html
"""

import json
from pathlib import Path
from fast_flights.core import parse_response
from fast_flights.primp import Response


def test_hybrid_parser():
    """Test the hybrid parser with debug_connecting_flights2.html"""
    
    # Read the debug HTML file
    debug_file = Path("debug_connecting_flights2.html")
    if not debug_file.exists():
        print(f"Error: {debug_file} not found")
        return
    
    html_content = debug_file.read_text(encoding="utf-8")
    
    # Create a mock Response object
    class MockResponse:
        def __init__(self, text):
            self.text = text
            self.text_markdown = text
            self.status_code = 200
    
    response = MockResponse(html_content)
    
    print("=== Testing Hybrid Parser with debug_connecting_flights2.html ===\n")
    
    try:
        result = parse_response(response, data_source='hybrid')
        print(f"Successfully parsed {len(result.flights)} flights")
        
        # Show detailed info for first few flights
        for i, flight in enumerate(result.flights[:5]):
            print(f"\n{'='*60}")
            print(f"Flight {i+1}:")
            print(f"  Route: {flight.departure_airport} → {flight.arrival_airport}")
            print(f"  Name: {flight.name}")
            print(f"  Price: ${flight.price}")
            print(f"  Stops: {flight.stops}")
            
            # Show new enriched data
            if flight.emissions:
                print(f"  Emissions: {flight.emissions}")
            if flight.operated_by:
                print(f"  Operated by: {flight.operated_by}")
            if flight.aircraft_details:
                print(f"  Aircraft: {flight.aircraft_details}")
            if flight.terminal_info:
                print(f"  Terminal info: {flight.terminal_info}")
            if flight.alliance:
                print(f"  Alliance: {flight.alliance}")
            if flight.on_time_performance is not None:
                print(f"  On-time performance: {flight.on_time_performance}%")
            
            # Show connection details if multi-segment
            if flight.connections:
                print(f"\n  Connections ({len(flight.connections)} segments):")
                for j, conn in enumerate(flight.connections):
                    print(f"    Segment {j+1}: {conn.departure_airport} → {conn.arrival_airport}")
                    print(f"      Flight: {conn.flight_number}")
                    print(f"      Time: {conn.departure} → {conn.arrival}")
                    print(f"      Duration: {conn.duration}")
                    if conn.aircraft:
                        print(f"      Aircraft: {conn.aircraft}")
                    if conn.operated_by:
                        print(f"      Operated by: {conn.operated_by}")
        
        # Summary of enrichments found
        print(f"\n{'='*60}")
        print("Summary of enrichments:")
        emissions_count = sum(1 for f in result.flights if f.emissions)
        operated_count = sum(1 for f in result.flights if f.operated_by)
        aircraft_count = sum(1 for f in result.flights if f.aircraft_details)
        terminal_count = sum(1 for f in result.flights if f.terminal_info)
        alliance_count = sum(1 for f in result.flights if f.alliance)
        ontime_count = sum(1 for f in result.flights if f.on_time_performance is not None)
        
        print(f"  Flights with emissions data: {emissions_count}")
        print(f"  Flights with operated by info: {operated_count}")
        print(f"  Flights with aircraft details: {aircraft_count}")
        print(f"  Flights with terminal info: {terminal_count}")
        print(f"  Flights with alliance info: {alliance_count}")
        print(f"  Flights with on-time performance: {ontime_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_hybrid_parser()