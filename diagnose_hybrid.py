#!/usr/bin/env python3
"""
Diagnose why hybrid mode has fewer results
"""

import os
from fast_flights.core import parse_response, extract_html_enrichments
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

print("DIAGNOSING HYBRID MODE")
print("=" * 70)

# Parse in HTML mode
html_result = parse_response(response, 'html')
print(f"HTML mode: {len(html_result.flights)} flights")

# Parse in JS mode
try:
    js_result = parse_response(response, 'js')
    print(f"JS mode: {len(js_result.flights)} flights")
except Exception as e:
    print(f"JS mode error: {e}")
    js_result = None

# Parse in hybrid mode
hybrid_result = parse_response(response, 'hybrid')
print(f"Hybrid mode: {len(hybrid_result.flights)} flights")

# Get HTML enrichments directly
parser = LexborHTMLParser(html_content)
enrichments = extract_html_enrichments(parser, html_content)
print(f"HTML enrichments found: {len(enrichments)}")

# Count enrichments with arrival_time_ahead
enrichments_with_time = sum(1 for e in enrichments if 'arrival_time_ahead' in e)
print(f"Enrichments with arrival_time_ahead: {enrichments_with_time}")

print("\nFIRST 5 ENRICHMENTS:")
for i, enrich in enumerate(enrichments[:5]):
    print(f"{i}: {enrich}")

print("\nPROBLEM ANALYSIS:")
print("1. JS parser returns fewer flights than HTML parser")
print("2. Enrichments are matched by index, not by flight identity")
print("3. This causes mismatched enrichments or missing enrichments")
print(f"4. Only first {len(hybrid_result.flights)} enrichments are used out of {len(enrichments)}")

# Check if JS flights have arrival_time_ahead
if js_result:
    js_with_time = sum(1 for f in js_result.flights if f.arrival_time_ahead and f.arrival_time_ahead.strip())
    print(f"\nJS flights with arrival_time_ahead: {js_with_time}")
    
# Check hybrid flights
hybrid_with_time = sum(1 for f in hybrid_result.flights if f.arrival_time_ahead and f.arrival_time_ahead.strip())
print(f"Hybrid flights with arrival_time_ahead: {hybrid_with_time}")

# Sample some flights to see the data
print("\nSAMPLE FLIGHTS WITH ARRIVAL_TIME_AHEAD:")
count = 0
for i, flight in enumerate(hybrid_result.flights):
    if flight.arrival_time_ahead and flight.arrival_time_ahead.strip():
        print(f"Flight {i}: {flight.name} - arrival_time_ahead='{flight.arrival_time_ahead}'")
        count += 1
        if count >= 3:
            break