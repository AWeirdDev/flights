#!/usr/bin/env python3.11
"""
Test aircraft extraction for both direct and connecting flights.
This script shows the complete data flow from JS parsing to final output.
"""

import json
import re
from pathlib import Path
from selectolax.lexbor import LexborHTMLParser
from fast_flights import FlightData, Passengers, create_filter
from fast_flights.bright_data_fetch import bright_data_fetch
from fast_flights.decoder import ResultDecoder
from fast_flights.core import convert_decoded_to_result, combine_results_structural

def trace_aircraft_data(decoded_result, final_result):
    """Trace aircraft data through the conversion pipeline."""
    print("=== Tracing Aircraft Data Through Pipeline ===\n")
    
    # Analyze decoded data
    all_decoded = decoded_result.best + decoded_result.other
    
    for idx, itinerary in enumerate(all_decoded):
        is_best = idx < len(decoded_result.best)
        flight_type = "Direct" if len(itinerary.flights) == 1 else "Connecting"
        
        print(f"\n{flight_type} Flight {idx + 1} ({'Best' if is_best else 'Other'}):")
        print(f"  Route: {itinerary.departure_airport} -> {itinerary.arrival_airport}")
        
        # Show aircraft for each segment
        print("  Segments:")
        for seg_idx, segment in enumerate(itinerary.flights):
            print(f"    Segment {seg_idx + 1}: {segment.departure_airport} -> {segment.arrival_airport}")
            print(f"      Flight: {segment.airline} {segment.flight_number}")
            print(f"      Aircraft: {segment.aircraft if segment.aircraft else 'None'}")
        
        # Find corresponding flight in final result
        matching_final = None
        for final_flight in final_result.flights:
            if (final_flight.departure_airport == itinerary.departure_airport and
                final_flight.arrival_airport == itinerary.arrival_airport and
                final_flight.is_best == is_best):
                matching_final = final_flight
                break
        
        if matching_final:
            print(f"  Final Output:")
            print(f"    aircraft_details: {matching_final.aircraft_details}")
            if matching_final.connections:
                print(f"    Connection aircraft data:")
                for conn in matching_final.connections:
                    print(f"      {conn.flight_number}: {conn.aircraft if conn.aircraft else 'None'}")
        else:
            print("  ❌ No matching flight found in final output!")

def test_multiple_routes():
    """Test different route types to see aircraft extraction patterns."""
    test_routes = [
        # Direct flight route
        {
            "name": "Direct: GCM -> JFK",
            "flight_data": [FlightData(date="2025-08-06", from_airport="GCM", to_airport="JFK")],
            "max_stops": 0
        },
        # Connecting flight route
        {
            "name": "Connecting: SFO -> JFK", 
            "flight_data": [FlightData(date="2025-08-06", from_airport="SFO", to_airport="JFK")],
            "max_stops": 2
        },
        # Mixed (both direct and connecting available)
        {
            "name": "Mixed: LAX -> JFK",
            "flight_data": [FlightData(date="2025-08-06", from_airport="LAX", to_airport="JFK")],
            "max_stops": None
        }
    ]
    
    for route in test_routes:
        print(f"\n{'='*80}")
        print(f"Testing: {route['name']}")
        print('='*80)
        
        filter_data = create_filter(
            flight_data=route["flight_data"],
            trip="one-way",
            passengers=Passengers(adults=1),
            seat="economy",
            max_stops=route["max_stops"]
        )
        
        params = {
            "tfs": filter_data.as_b64().decode("utf-8"),
            "hl": "en",
            "tfu": "EgQIABABIgA",
            "curr": "",
        }
        
        try:
            response = bright_data_fetch(params)
            parser = LexborHTMLParser(response.text)
            
            # Extract and decode JS data
            script = parser.css_first(r'script.ds\:1').text()
            match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script)
            data = json.loads(match.group(1))
            decoded = ResultDecoder.decode(data)
            
            # Convert to result (this is where we lose aircraft for direct flights)
            js_result = convert_decoded_to_result(decoded)
            
            # Apply HTML enrichments
            final_result = combine_results_structural(js_result, parser)
            
            # Trace the data
            trace_aircraft_data(decoded, final_result)
            
            # Summary for this route
            total_flights = len(final_result.flights)
            direct_flights = sum(1 for f in final_result.flights if f.stops == 0)
            connecting_flights = total_flights - direct_flights
            
            direct_with_aircraft = sum(1 for f in final_result.flights 
                                     if f.stops == 0 and f.aircraft_details)
            connecting_with_aircraft = sum(1 for f in final_result.flights 
                                         if f.stops > 0 and f.aircraft_details)
            
            print(f"\n📊 Summary for {route['name']}:")
            print(f"  Total flights: {total_flights}")
            print(f"  Direct flights: {direct_flights} ({direct_with_aircraft} with aircraft)")
            print(f"  Connecting flights: {connecting_flights} ({connecting_with_aircraft} with aircraft)")
            
        except Exception as e:
            print(f"Error testing {route['name']}: {e}")
            import traceback
            traceback.print_exc()

def analyze_conversion_function():
    """Analyze the convert_decoded_to_result function to see where aircraft is handled."""
    print("\n" + "="*80)
    print("Analyzing convert_decoded_to_result function")
    print("="*80)
    
    print("\nKey observations from code analysis:")
    print("1. For connecting flights (lines 319-333 in core.py):")
    print("   - Aircraft data IS extracted from connections")
    print("   - If all segments use same aircraft, it's set as flight.aircraft_details")
    print("   - If segments use different aircraft, they're joined with ' / '")
    
    print("\n2. For direct flights:")
    print("   - Connections list is None (line 577)")
    print("   - No code sets aircraft_details for direct flights")
    print("   - Aircraft data exists in itinerary.flights[0].aircraft but isn't used")
    
    print("\n3. The fix location:")
    print("   - After creating the Flight object (around line 579)")
    print("   - Check if flight.stops == 0 and flight.aircraft_details is None")
    print("   - Set flight.aircraft_details = itinerary.flights[0].aircraft")

def main():
    print("Testing Aircraft Extraction for Direct and Connecting Flights\n")
    
    # Test multiple routes
    test_multiple_routes()
    
    # Analyze the conversion function
    analyze_conversion_function()
    
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("="*80)
    print("\n✅ Aircraft data IS available in JS for direct flights")
    print("❌ It's NOT being transferred to aircraft_details field")
    print("📍 The issue is in convert_decoded_to_result function")
    print("🔧 Fix needed: Add aircraft extraction for direct flights (0 stops)")

if __name__ == "__main__":
    main()