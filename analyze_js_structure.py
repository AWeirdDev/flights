#!/usr/bin/env python3
"""
Analyze the JavaScript nested array structure to find where individual
flight segment departure/arrival times are stored.
"""

import re
import json
from pathlib import Path

def find_nested_arrays(data, path=[], depth=0, max_depth=10):
    """Recursively explore nested arrays looking for time-like patterns."""
    if depth > max_depth:
        return
        
    if isinstance(data, list):
        for i, item in enumerate(data):
            current_path = path + [i]
            
            # Check if this looks like a time tuple [hour, minute]
            if (isinstance(item, list) and len(item) == 2 and 
                all(isinstance(x, (int, float)) for x in item) and
                0 <= item[0] <= 23 and 0 <= item[1] <= 59):
                print(f"Potential time at path {current_path}: {item}")
                
            # Check for flight-like data structures
            if isinstance(item, list) and len(item) > 10:
                # Look for patterns that match the FlightDecoder structure
                # Based on decoder.py, times are at indices [8] and [10]
                if len(item) > 10:
                    try:
                        if (isinstance(item[8], list) and len(item[8]) == 2 and
                            isinstance(item[10], list) and len(item[10]) == 2):
                            print(f"\nPotential flight data at path {current_path}:")
                            print(f"  Departure time (index 8): {item[8]}")
                            print(f"  Arrival time (index 10): {item[10]}")
                            
                            # Check for airport codes
                            if len(item) > 6 and isinstance(item[3], str) and isinstance(item[5], str):
                                print(f"  Departure airport (index 3): {item[3]}")
                                print(f"  Arrival airport (index 5): {item[5]}")
                                
                            # Check for travel time
                            if len(item) > 11 and isinstance(item[11], (int, float)):
                                print(f"  Travel time (index 11): {item[11]} minutes")
                    except:
                        pass
                        
            find_nested_arrays(item, current_path, depth + 1, max_depth)
            
    elif isinstance(data, dict):
        for key, value in data.items():
            find_nested_arrays(value, path + [key], depth + 1, max_depth)

def extract_js_data(html_content):
    """Extract JavaScript data array from the HTML."""
    # Look for script tag with class="ds:1"
    script_pattern = r'<script[^>]*class="ds:1"[^>]*>(.*?)</script>'
    script_match = re.search(script_pattern, html_content, re.DOTALL)
    
    if not script_match:
        print("Could not find script with class='ds:1'")
        return None
        
    script_content = script_match.group(1)
    
    # Extract the data array
    data_pattern = r'data:\s*(\[.*?\])(?=,|\s*\})'
    data_match = re.search(data_pattern, script_content, re.DOTALL)
    
    if not data_match:
        print("Could not find data array in script")
        return None
        
    try:
        # Clean up the data string and parse it
        data_str = data_match.group(1)
        # Parse the JSON data
        data = json.loads(data_str)
        return data
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        # Try to clean up common issues
        # Remove any trailing commas
        data_str = re.sub(r',\s*(?=\]|\})', '', data_str)
        try:
            data = json.loads(data_str)
            return data
        except:
            return None

def analyze_itinerary_structure(data):
    """Analyze the structure based on the decoder patterns."""
    print("\n=== Analyzing based on decoder.py structure ===")
    
    # According to ResultDecoder:
    # BEST: DecoderKey[List[Itinerary]] = DecoderKey([2, 0], ...)
    # OTHER: DecoderKey[List[Itinerary]] = DecoderKey([3, 0], ...)
    
    if not isinstance(data, list) or len(data) < 4:
        print("Data doesn't match expected structure")
        return
        
    # Check for best flights
    if len(data) > 2 and isinstance(data[2], list) and len(data[2]) > 0:
        print("\nBest flights found at data[2][0]:")
        analyze_flights(data[2][0], "Best")
        
    # Check for other flights  
    if len(data) > 3 and isinstance(data[3], list) and len(data[3]) > 0:
        print("\nOther flights found at data[3][0]:")
        analyze_flights(data[3][0], "Other")

def analyze_flights(flight_list, category):
    """Analyze individual flights based on ItineraryDecoder structure."""
    for i, itinerary in enumerate(flight_list[:3]):  # First 3 flights
        if not isinstance(itinerary, list) or len(itinerary) < 1:
            continue
            
        print(f"\n{category} Flight {i+1}:")
        
        # According to ItineraryDecoder:
        # FLIGHTS: DecoderKey[List[Flight]] = DecoderKey([0, 2], ...)
        if (isinstance(itinerary[0], list) and len(itinerary[0]) > 2 and 
            isinstance(itinerary[0][2], list)):
            
            flights = itinerary[0][2]
            print(f"  Number of segments: {len(flights)}")
            
            for j, flight in enumerate(flights):
                if isinstance(flight, list) and len(flight) > 21:
                    print(f"\n  Segment {j+1}:")
                    
                    # FlightDecoder indices:
                    # DEPARTURE_TIME: DecoderKey = DecoderKey([8])
                    # ARRIVAL_TIME: DecoderKey = DecoderKey([10])
                    # TRAVEL_TIME: DecoderKey = DecoderKey([11])
                    # DEPARTURE_AIRPORT: DecoderKey = DecoderKey([3])
                    # ARRIVAL_AIRPORT: DecoderKey = DecoderKey([5])
                    
                    if len(flight) > 8 and isinstance(flight[8], list):
                        print(f"    Departure time: {flight[8]}")
                    if len(flight) > 10 and isinstance(flight[10], list):
                        print(f"    Arrival time: {flight[10]}")
                    if len(flight) > 11:
                        print(f"    Travel time: {flight[11]} minutes")
                    if len(flight) > 3:
                        print(f"    Departure airport: {flight[3]}")
                    if len(flight) > 5:
                        print(f"    Arrival airport: {flight[5]}")
                        
            # Check for layovers
            # LAYOVERS: DecoderKey = DecoderKey([0, 13], ...)
            if (isinstance(itinerary[0], list) and len(itinerary[0]) > 13 and
                isinstance(itinerary[0][13], list)):
                layovers = itinerary[0][13]
                if layovers:
                    print(f"\n  Layovers: {len(layovers)}")
                    for k, layover in enumerate(layovers):
                        if isinstance(layover, list) and len(layover) > 0:
                            print(f"    Layover {k+1}: {layover[0]} minutes")

def main():
    # Read the debug HTML file
    debug_file = Path("debug_connecting_flights.html")
    if not debug_file.exists():
        print(f"Error: {debug_file} not found")
        return
    
    html_content = debug_file.read_text(encoding="utf-8")
    
    # Extract and analyze JavaScript data
    data = extract_js_data(html_content)
    if data:
        print("Successfully extracted JavaScript data")
        print(f"Top-level structure: list with {len(data)} elements")
        
        # Analyze based on decoder structure
        analyze_itinerary_structure(data)
        
        # Also do a general recursive search
        print("\n\n=== General recursive search for time patterns ===")
        find_nested_arrays(data, max_depth=8)
    else:
        print("Failed to extract JavaScript data")

if __name__ == "__main__":
    main()