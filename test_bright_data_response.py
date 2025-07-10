#!/usr/bin/env python3
"""
Test Bright Data response handling for round-trip flights
"""

import os
import re
from datetime import datetime, timedelta
from fast_flights import create_filter, FlightData, Passengers
from fast_flights.bright_data_fetch import bright_data_fetch
from selectolax.lexbor import LexborHTMLParser

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

print("Testing Bright Data Response for Round-Trip")
print("=" * 60)

# Prepare params
params = {
    "tfs": filter.as_b64().decode('utf-8'),
    "hl": "en",
    "tfu": "EgQIABABIgA",
    "curr": "",
}

# Build the URL that Bright Data will fetch
google_url = "https://www.google.com/travel/flights?" + "&".join(f"{k}={v}" for k, v in params.items())
print(f"Google Flights URL: {google_url}")
print()

# Get response from Bright Data
print("Fetching from Bright Data...")
res = bright_data_fetch(params)
print(f"Response status: {res.status_code}")
print(f"Response length: {len(res.text)} characters")

# Parse the response
parser = LexborHTMLParser(res.text)

# Look for any tabs or navigation elements that might indicate round-trip structure
print("\n--- Looking for Round-Trip UI Elements ---")

# Check for tab elements
tabs = parser.css('[role="tab"]')
if tabs:
    print(f"Found {len(tabs)} tabs:")
    for i, tab in enumerate(tabs):
        tab_text = tab.text(strip=True)
        print(f"  Tab {i}: {tab_text}")

# Check for any elements with date information
date_elements = parser.css('[aria-label*="2025"]')
print(f"\nFound {len(date_elements)} elements with 2025 dates")

# Look for direction indicators in the HTML
print("\n--- Direction Analysis ---")

# Count occurrences of directional patterns
outbound_patterns = ["JFK to LAX", "JFK–LAX", "JFK - LAX", "from JFK", "to LAX"]
return_patterns = ["LAX to JFK", "LAX–JFK", "LAX - JFK", "from LAX", "to JFK"]

outbound_count = 0
return_count = 0

for pattern in outbound_patterns:
    outbound_count += res.text.count(pattern)

for pattern in return_patterns:
    return_count += res.text.count(pattern)

print(f"Outbound direction indicators: {outbound_count}")
print(f"Return direction indicators: {return_count}")

# Check if there's any JavaScript that might handle tab switching
print("\n--- JavaScript Analysis ---")
scripts = parser.css('script')
print(f"Found {len(scripts)} script tags")

# Look for any script that might contain routing data
routing_scripts = 0
for script in scripts:
    content = script.text()
    if content and ("LAX" in content or "JFK" in content):
        routing_scripts += 1

print(f"Scripts containing airport codes: {routing_scripts}")

# Save a smaller debug file with just the relevant parts
print("\n--- Saving Debug Output ---")
with open('bright_data_roundtrip_response.html', 'w') as f:
    f.write(res.text)
print("Full response saved to bright_data_roundtrip_response.html")

# Extract just the flight containers for easier analysis
containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
with open('bright_data_flight_containers.html', 'w') as f:
    f.write("<html><body>\n")
    for i, container in enumerate(containers):
        f.write(f"<!-- Container {i} -->\n")
        f.write(str(container.html))
        f.write("\n\n")
    f.write("</body></html>")
print("Flight containers saved to bright_data_flight_containers.html")

print("\n--- Conclusion ---")
if return_count > 0:
    print("✓ Return flight indicators found - Bright Data IS returning round-trip data")
else:
    print("✗ No return flight indicators - Bright Data appears to only return outbound data")
    print("  This might be because:")
    print("  1. Bright Data needs additional parameters to fetch round-trip data")
    print("  2. Google Flights loads return flights dynamically via JavaScript")
    print("  3. The round-trip data is in a different format than expected")