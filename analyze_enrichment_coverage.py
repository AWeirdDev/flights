#!/usr/bin/env python3
"""
Analyze enrichment coverage to understand the matching issue
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

with open(test_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

response = MockResponse(html_content)
parser = LexborHTMLParser(html_content)

# Get data
js_result = parse_response(response, 'js')
enrichments = extract_html_enrichments(parser, html_content)

print("ENRICHMENT COVERAGE ANALYSIS")
print("=" * 70)
print(f"JS flights: {len(js_result.flights)}")
print(f"HTML enrichments: {len(enrichments)}")

# Analyze enrichments
enrichments_with_url = sum(1 for e in enrichments if 'url' in e and e['url'])
enrichments_with_time = sum(1 for e in enrichments if 'arrival_time_ahead' in e)
enrichments_with_time_and_url = sum(1 for e in enrichments if 'arrival_time_ahead' in e and 'url' in e and e['url'])
enrichments_with_time_no_url = sum(1 for e in enrichments if 'arrival_time_ahead' in e and ('url' not in e or not e['url']))

print(f"\nEnrichments with URL: {enrichments_with_url}")
print(f"Enrichments with arrival_time_ahead: {enrichments_with_time}")
print(f"Enrichments with both: {enrichments_with_time_and_url}")
print(f"Enrichments with time but no URL: {enrichments_with_time_no_url}")

# Check first 108 enrichments (what would be used by index matching)
first_108_with_time = sum(1 for e in enrichments[:108] if 'arrival_time_ahead' in e)
print(f"\nFirst 108 enrichments with arrival_time_ahead: {first_108_with_time}")

# Show some enrichments without URLs
print(f"\nEXAMPLES OF ENRICHMENTS WITHOUT URLS:")
count = 0
for i, e in enumerate(enrichments):
    if 'url' not in e or not e['url']:
        print(f"Enrichment {i}: {e}")
        count += 1
        if count >= 3:
            break

# Check distribution of arrival_time_ahead
print(f"\nDISTRIBUTION OF ARRIVAL_TIME_AHEAD IN ENRICHMENTS:")
for i in range(0, len(enrichments), 20):
    chunk_end = min(i + 20, len(enrichments))
    chunk_with_time = sum(1 for e in enrichments[i:chunk_end] if 'arrival_time_ahead' in e)
    print(f"  Enrichments {i}-{chunk_end}: {chunk_with_time} with arrival_time_ahead")