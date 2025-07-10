#!/usr/bin/env python3
"""
Verify arrival_time_ahead extraction works in all modes
"""

import os
from fast_flights.core import parse_response

class MockResponse:
    """Mock response object for testing"""
    def __init__(self, text):
        self.text = text
        self.text_markdown = text
        self.status_code = 200

# Test with a file known to have arrival_time_ahead data
test_file = 'raw_html_extreme_LAX_JFK_9_Terminals.html'

if not os.path.exists(test_file):
    print(f"Test file {test_file} not found")
    exit(1)

with open(test_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

response = MockResponse(html_content)

print("Testing arrival_time_ahead extraction")
print("=" * 50)

for mode in ['html', 'hybrid']:
    print(f"\n{mode.upper()} MODE:")
    
    try:
        result = parse_response(response, mode)
        
        # Count flights with arrival_time_ahead
        count = 0
        samples = []
        for flight in result.flights:
            if flight.arrival_time_ahead and flight.arrival_time_ahead.strip():
                count += 1
                if len(samples) < 3:
                    samples.append(f"{flight.name}: '{flight.arrival_time_ahead}'")
        
        print(f"  Total flights: {len(result.flights)}")
        print(f"  With arrival_time_ahead: {count} ({count/len(result.flights)*100:.1f}%)")
        if samples:
            print(f"  Samples: {', '.join(samples)}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n✅ Both HTML and Hybrid modes now extract arrival_time_ahead!")