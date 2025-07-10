#!/usr/bin/env python3.11
"""
Debug script to check if aircraft data is available in JS data for direct flights.
This will help us understand where the aircraft_details field is being lost.
"""

import json
import re
from pathlib import Path
from selectolax.lexbor import LexborHTMLParser
from fast_flights import FlightData, Passengers, create_filter
from fast_flights.bright_data_fetch import bright_data_fetch
from fast_flights.decoder import ResultDecoder

def analyze_js_data(html_content):
    """Extract and analyze JS data structure."""
    print("=== Analyzing JS Data ===\n")
    
    # Extract JS data
    parser = LexborHTMLParser(html_content)
    script = parser.css_first(r'script.ds\:1')
    if not script:
        print("ERROR: Could not find script with JS data")
        return None, None
        
    script_text = script.text()
    match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script_text)
    if not match:
        print("ERROR: Could not extract data from script")
        return None, None
        
    data = json.loads(match.group(1))
    
    # Decode the data
    try:
        decoded = ResultDecoder.decode(data)
        if not decoded:
            print("ERROR: Could not decode data")
            return None, None
    except Exception as e:
        print(f"ERROR decoding data: {e}")
        print(f"Data structure: {json.dumps(data, indent=2)[:500]}...")
        return None, None
    
    print(f"Found {len(decoded.best)} best flights and {len(decoded.other)} other flights")
    
    # Look for direct flights
    direct_flights = []
    all_flights = decoded.best + decoded.other
    
    for idx, itinerary in enumerate(all_flights):
        is_best = idx < len(decoded.best)
        num_segments = len(itinerary.flights)
        
        if num_segments == 1:  # Direct flight
            flight = itinerary.flights[0]
            direct_flights.append({
                'is_best': is_best,
                'airline': flight.airline,
                'airline_name': flight.airline_name,
                'flight_number': f"{flight.airline} {flight.flight_number}",
                'route': f"{flight.departure_airport} -> {flight.arrival_airport}",
                'aircraft': flight.aircraft,  # This is what we're looking for!
                'departure_time': flight.departure_time,
                'arrival_time': flight.arrival_time,
                'operator': flight.operator,
            })
    
    return direct_flights, decoded

def analyze_final_output(result):
    """Analyze the final output after processing."""
    print("\n=== Analyzing Final Output ===\n")
    
    direct_flights = []
    for flight in result.flights:
        if flight.stops == 0:  # Direct flight
            direct_flights.append({
                'is_best': flight.is_best,
                'name': flight.name,
                'flight_number': flight.flight_number,
                'route': f"{flight.departure_airport} -> {flight.arrival_airport}",
                'aircraft_details': flight.aircraft_details,  # This is what's missing!
                'connections': flight.connections,
                'departure': flight.departure,
                'arrival': flight.arrival,
            })
    
    return direct_flights

def main():
    print("Debug: Checking aircraft data for direct flights\n")
    
    # Create filter for a route likely to have direct flights
    # Using LAX to JFK which typically has many direct flights
    filter_data = create_filter(
        flight_data=[
            FlightData(
                date="2025-08-06",
                from_airport="LAX",
                to_airport="JFK",
            ),
        ],
        trip="one-way",
        passengers=Passengers(adults=1),
        seat="economy",
        max_stops=None  # Allow any to see both direct and connecting
    )
    
    print(f"Filter URL: https://www.google.com/travel/flights?tfs={filter_data.as_b64().decode('utf-8')}")
    
    # Get the response using Bright Data
    params = {
        "tfs": filter_data.as_b64().decode("utf-8"),
        "hl": "en",
        "tfu": "EgQIABABIgA",
        "curr": "",
    }
    
    print("\nFetching data from Bright Data...")
    response = bright_data_fetch(params)
    
    # Save HTML for reference
    debug_file = Path("debug_direct_flights.html")
    debug_file.write_text(response.text, encoding="utf-8")
    print(f"Saved HTML to {debug_file}")
    
    # Analyze JS data
    js_direct_flights, decoded = analyze_js_data(response.text)
    
    if js_direct_flights:
        print(f"\nFound {len(js_direct_flights)} direct flights in JS data:")
        for i, flight in enumerate(js_direct_flights, 1):
            print(f"\nDirect Flight {i} (JS Data):")
            print(f"  Route: {flight['route']}")
            print(f"  Flight: {flight['flight_number']}")
            print(f"  Airline: {flight['airline_name']}")
            print(f"  Aircraft: {flight['aircraft']}")  # <-- Key field!
            print(f"  Operator: {flight['operator']}")
            print(f"  Is Best: {flight['is_best']}")
    else:
        print("\nNo direct flights found in JS data")
    
    # Now process with hybrid mode to see final output
    print("\n" + "="*60)
    print("Processing with hybrid mode...")
    
    from fast_flights.core import parse_response
    result = parse_response(response, 'hybrid')
    
    # Analyze final output
    final_direct_flights = analyze_final_output(result)
    
    if final_direct_flights:
        print(f"\nFound {len(final_direct_flights)} direct flights in final output:")
        for i, flight in enumerate(final_direct_flights, 1):
            print(f"\nDirect Flight {i} (Final Output):")
            print(f"  Route: {flight['route']}")
            print(f"  Flight: {flight['flight_number']}")
            print(f"  Name: {flight['name']}")
            print(f"  Aircraft Details: {flight['aircraft_details']}")  # <-- Should be populated!
            print(f"  Has Connections: {flight['connections'] is not None}")
            print(f"  Is Best: {flight['is_best']}")
    
    # Compare results
    print("\n" + "="*60)
    print("COMPARISON SUMMARY:")
    print(f"Direct flights in JS data: {len(js_direct_flights)}")
    print(f"Direct flights in final output: {len(final_direct_flights)}")
    
    if js_direct_flights and final_direct_flights:
        js_has_aircraft = sum(1 for f in js_direct_flights if f['aircraft'])
        final_has_aircraft = sum(1 for f in final_direct_flights if f['aircraft_details'])
        
        print(f"\nJS flights with aircraft data: {js_has_aircraft}/{len(js_direct_flights)}")
        print(f"Final flights with aircraft_details: {final_has_aircraft}/{len(final_direct_flights)}")
        
        if js_has_aircraft > 0 and final_has_aircraft == 0:
            print("\n❌ ISSUE CONFIRMED: Aircraft data exists in JS but not in final output!")
            print("   The data is being lost during the conversion process.")
        elif js_has_aircraft == 0:
            print("\n⚠️  No aircraft data found in JS data either.")
            print("   This might be a data availability issue.")
        else:
            print("\n✅ Aircraft data is being preserved correctly.")

if __name__ == "__main__":
    main()