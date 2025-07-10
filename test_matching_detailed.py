#!/usr/bin/env python3
"""
Test matching with detailed output
"""

import os
from fast_flights.core import parse_response
from selectolax.lexbor import LexborHTMLParser

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

# Parse in hybrid mode with some temporary debug code
# We'll manually check a few flights
from fast_flights.core import extract_html_enrichments
parser = LexborHTMLParser(html_content)
js_result = parse_response(response, 'js')
enrichments = extract_html_enrichments(parser, html_content)

# Create enrichment mapping
enrichment_by_url = {}
for enrichment in enrichments:
    if 'url' in enrichment and enrichment['url']:
        enrichment_by_url[enrichment['url']] = enrichment

print("TESTING FLIGHT MATCHING")
print("=" * 70)

# Test matching for first few flights
for i in range(min(10, len(js_result.flights))):
    flight = js_result.flights[i]
    print(f"\nFlight {i}: {flight.name}")
    print(f"  flight_number: {flight.flight_number}")
    print(f"  airports: {flight.departure_airport} -> {flight.arrival_airport}")
    
    if flight.flight_number:
        flight_num_for_url = flight.flight_number.replace(' ', '-')
        print(f"  flight_num_for_url: {flight_num_for_url}")
        
        # Try to find match
        matched = False
        for url, enrich in enrichment_by_url.items():
            if flight_num_for_url in url:
                # Check patterns
                direct_pattern = f"{flight.departure_airport}-{flight.arrival_airport}-{flight_num_for_url}"
                if direct_pattern in url:
                    print(f"  ✅ DIRECT MATCH: {url}")
                    if 'arrival_time_ahead' in enrich:
                        print(f"     arrival_time_ahead: {enrich['arrival_time_ahead']}")
                    matched = True
                    break
                elif f"{flight.departure_airport}-" in url and flight_num_for_url in url.split(',')[0]:
                    print(f"  ✅ CONNECTING MATCH: {url}")
                    if 'arrival_time_ahead' in enrich:
                        print(f"     arrival_time_ahead: {enrich['arrival_time_ahead']}")
                    matched = True
                    break
        
        if not matched:
            print(f"  ❌ NO MATCH FOUND")

# Now run the actual hybrid parse
print("\n\nACTUAL HYBRID RESULT:")
hybrid_result = parse_response(response, 'hybrid')
hybrid_with_time = sum(1 for f in hybrid_result.flights if f.arrival_time_ahead and f.arrival_time_ahead.strip())
print(f"Flights with arrival_time_ahead: {hybrid_with_time}/{len(hybrid_result.flights)}")