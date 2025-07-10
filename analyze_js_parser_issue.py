#!/usr/bin/env python3
"""
Analyze why JS parser finds only 108 flights when there are 218 visible
"""

import json
import re
from fast_flights.decoder import ResultDecoder

# Read the HTML file
test_file = 'raw_html_extreme_LAX_JFK_9_Terminals.html'
with open(test_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

print("ANALYZING JS PARSER ISSUE")
print("=" * 70)

# Extract the JS data
script_match = re.search(r'<script[^>]*class="ds:1"[^>]*>(.*?)</script>', html_content, re.DOTALL)
if not script_match:
    print("ERROR: Could not find script tag with class='ds:1'")
    exit(1)

script_content = script_match.group(1)
print(f"Script content length: {len(script_content)} chars")

# Extract the data array
match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script_content)
if not match:
    print("ERROR: Could not extract data array from script")
    exit(1)

data_str = match.group(1)
print(f"Data array length: {len(data_str)} chars")

# Parse JSON
try:
    data = json.loads(data_str)
    print(f"Parsed JSON successfully")
    print(f"Top-level array length: {len(data)}")
except Exception as e:
    print(f"ERROR parsing JSON: {e}")
    exit(1)

# Decode using ResultDecoder
try:
    decoded = ResultDecoder.decode(data)
    if decoded:
        print(f"\nDecoded Result:")
        print(f"  Best flights: {len(decoded.best)}")
        print(f"  Other flights: {len(decoded.other)}")
        print(f"  Total: {len(decoded.best) + len(decoded.other)}")
        
        # Check if there are multiple price options per flight
        print(f"\nFirst few flights:")
        all_flights = decoded.best + decoded.other
        for i, flight in enumerate(all_flights[:5]):
            print(f"\nFlight {i+1}:")
            print(f"  Airlines: {flight.airline_names}")
            print(f"  Segments: {len(flight.flights)}")
            if hasattr(flight, 'price_options'):
                print(f"  Price options: {len(flight.price_options) if flight.price_options else 0}")
            if hasattr(flight.itinerary_summary, 'price'):
                print(f"  Price: ${flight.itinerary_summary.price}")
            else:
                print(f"  Price: Not found")
                
    else:
        print("ERROR: Decoder returned None")
except Exception as e:
    print(f"ERROR decoding: {e}")
    import traceback
    traceback.print_exc()

# Let's look at the raw structure to understand better
print(f"\n\nRAW DATA STRUCTURE ANALYSIS:")
print(f"Type of data: {type(data)}")
if isinstance(data, list):
    print(f"Length: {len(data)}")
    
    # Check first few elements
    for i in range(min(5, len(data))):
        elem = data[i]
        if isinstance(elem, list):
            print(f"\nElement {i}: list of length {len(elem)}")
            # Show structure of nested lists
            for j in range(min(3, len(elem))):
                sub_elem = elem[j]
                if isinstance(sub_elem, list):
                    print(f"  [{j}]: list of length {len(sub_elem)}")
                else:
                    print(f"  [{j}]: {type(sub_elem).__name__} = {str(sub_elem)[:50]}...")
        else:
            print(f"\nElement {i}: {type(elem).__name__} = {str(elem)[:100]}...")

# Check if there's price/class data that might triple the count
print(f"\n\nHYPOTHESIS: Each flight has 3 price classes (economy, premium, business)")
print(f"Visual prices: 648")
print(f"Visual flights: 218") 
print(f"Ratio: {648 / 218:.1f} prices per flight")
print(f"\nThis suggests each flight appears 3 times with different prices")
print(f"JS parser might be consolidating these into single flights")