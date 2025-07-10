#!/usr/bin/env python3
"""
Debug flight matching between JS and HTML
"""

import os
from fast_flights.core import parse_response, extract_html_enrichments
from selectolax.lexbor import LexborHTMLParser
import json

class MockResponse:
    """Mock response object for testing"""
    def __init__(self, text):
        self.text = text
        self.text_markdown = text
        self.status_code = 200

# Test with a file
test_file = 'raw_html_extreme_LAX_JFK_9_Terminals.html'

if not os.path.exists(test_file):
    print(f"Test file {test_file} not found")
    exit(1)

with open(test_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

response = MockResponse(html_content)

# Parse in JS mode to see what flight data we have
js_result = parse_response(response, 'js')

# Get HTML enrichments
parser = LexborHTMLParser(html_content)
enrichments = extract_html_enrichments(parser, html_content)

print("DEBUGGING FLIGHT MATCHING")
print("=" * 70)

# Show first few JS flights
print("\nFIRST 5 JS FLIGHTS:")
for i, flight in enumerate(js_result.flights[:5]):
    print(f"\nFlight {i}:")
    print(f"  name: {flight.name}")
    print(f"  flight_number: {flight.flight_number}")
    print(f"  departure_airport: {flight.departure_airport}")
    print(f"  arrival_airport: {flight.arrival_airport}")
    print(f"  arrival_time_ahead: '{flight.arrival_time_ahead}'")

# Show enrichments with arrival_time_ahead
print("\n\nENRICHMENTS WITH ARRIVAL_TIME_AHEAD:")
count = 0
for i, enrich in enumerate(enrichments):
    if 'arrival_time_ahead' in enrich:
        print(f"\nEnrichment {i}:")
        print(f"  arrival_time_ahead: {enrich['arrival_time_ahead']}")
        print(f"  url: {enrich.get('url', 'No URL')}")
        count += 1
        if count >= 5:
            break

# Try to understand the URL pattern
print("\n\nURL PATTERN ANALYSIS:")
for i, enrich in enumerate(enrichments[:10]):
    if 'url' in enrich:
        url = enrich['url']
        # Extract itinerary part
        if 'itinerary=' in url:
            itinerary = url.split('itinerary=')[1]
            print(f"{i}: {itinerary}")

print("\n\nMATCHING ISSUES:")
print("1. JS flight_number format: 'AA 274' (with space)")
print("2. URL format: 'AA-274' (with hyphen)")
print("3. Multi-segment flights have complex URLs")
print("4. Need to handle both direct and connecting flights")