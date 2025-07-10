#!/usr/bin/env python3
"""
Diagnose return flight parsing issue with Bright Data
"""

import os
import json
from datetime import datetime, timedelta
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers
from fast_flights.bright_data_fetch import bright_data_fetch
from selectolax.lexbor import LexborHTMLParser
import re

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

# Test configuration
test_date = datetime.now() + timedelta(days=30)
return_date = test_date + timedelta(days=7)

# Create a round-trip filter
filter = create_filter(
    flight_data=[
        FlightData(
            date=test_date.strftime("%Y-%m-%d"),
            from_airport="JFK",
            to_airport="LAX",
        ),
        FlightData(
            date=return_date.strftime("%Y-%m-%d"),
            from_airport="LAX",
            to_airport="JFK",
        )
    ],
    trip="round-trip",
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
    max_stops=None,
)

print("Diagnosing Return Flight Parsing")
print("=" * 60)
print(f"Filter URL: https://www.google.com/travel/flights?tfs={filter.as_b64().decode('utf-8')}")
print()

# Get the raw HTML from Bright Data
params = {
    "tfs": filter.as_b64().decode('utf-8'),
    "hl": "en",
    "tfu": "EgQIABABIgA",
    "curr": "",
}

# Get response
res = bright_data_fetch(params)
parser = LexborHTMLParser(res.text)

# Save HTML for inspection
with open('debug_return_flights.html', 'w') as f:
    f.write(res.text)
print("Saved HTML to debug_return_flights.html")

# Analyze the HTML structure
print("\n--- HTML Structure Analysis ---")

# Get all flight containers
flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
print(f"Found {len(flight_containers)} flight containers")

# Check container sizes
container_sizes = []
for i, container in enumerate(flight_containers):
    items = container.css("ul.Rk10dc li")
    container_sizes.append(len(items))
    print(f"Container {i}: {len(items)} flight items")

# Look for any indication of return flights
print("\n--- Searching for Return Flight Indicators ---")

# Check for any LAX-JFK references in the HTML
lax_jfk_count = res.text.count("LAX-JFK")
jfk_lax_count = res.text.count("JFK-LAX")
print(f"JFK-LAX references: {jfk_lax_count}")
print(f"LAX-JFK references: {lax_jfk_count}")

# Check for date references
outbound_date_str = test_date.strftime("%Y%m%d")
return_date_str = return_date.strftime("%Y%m%d")
outbound_date_count = res.text.count(outbound_date_str)
return_date_count = res.text.count(return_date_str)
print(f"Outbound date ({outbound_date_str}) references: {outbound_date_count}")
print(f"Return date ({return_date_str}) references: {return_date_count}")

# Look for specific return flight indicators
print("\n--- Checking for Round-Trip Structure ---")

# Check if there's a tab or section structure for outbound/return
tabs = parser.css('[role="tab"], [role="tabpanel"]')
print(f"Found {len(tabs)} tab elements")

# Look for any elements with text containing "Return" or "Outbound"
return_elements = parser.css('*:contains("Return")')
outbound_elements = parser.css('*:contains("Outbound")')
print(f"Elements with 'Return': {len(return_elements)}")
print(f"Elements with 'Outbound': {len(outbound_elements)}")

# Try to find JS data
print("\n--- JS Data Analysis ---")
try:
    script = parser.css_first(r'script.ds\:1').text()
    match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script)
    if match:
        data = json.loads(match.group(1))
        print(f"JS data found with {len(data)} elements")
        
        # Look for structure that might indicate return flights
        if isinstance(data, list) and len(data) > 0:
            # Check first few elements
            for i in range(min(3, len(data))):
                if isinstance(data[i], list) and len(data[i]) > 6:
                    # Check for airport codes at positions that typically contain them
                    if len(data[i]) > 13 and isinstance(data[i][13], list):
                        print(f"Element {i}: Possible airports: {data[i][13]}")
                    if len(data[i]) > 12 and isinstance(data[i][12], list):
                        print(f"Element {i}: More data: {data[i][12][:5]}...")  # First 5 items
except Exception as e:
    print(f"Error parsing JS data: {e}")

print("\n--- Conclusion ---")
if lax_jfk_count > 0:
    print("✓ Return flight data (LAX-JFK) IS present in the HTML")
    print("  This suggests the issue is in the parsing logic, not the data retrieval")
else:
    print("✗ Return flight data (LAX-JFK) is NOT present in the HTML")
    print("  This suggests Bright Data might be returning only outbound results")

# Try running the full parser to see what it extracts
print("\n--- Running Full Parser ---")
try:
    result = get_flights_from_filter(filter, mode="bright-data", data_source='hybrid')
    
    outbound = sum(1 for f in result.flights if f.departure_airport == "JFK" and f.arrival_airport == "LAX")
    returns = sum(1 for f in result.flights if f.departure_airport == "LAX" and f.arrival_airport == "JFK")
    
    print(f"Parser found {len(result.flights)} total flights")
    print(f"  Outbound (JFK→LAX): {outbound}")
    print(f"  Return (LAX→JFK): {returns}")
except Exception as e:
    print(f"Parser error: {e}")