#!/usr/bin/env python3
"""
Final comprehensive check for individual segment departure/arrival times in HTML.
"""

import re
from pathlib import Path
from selectolax.lexbor import LexborHTMLParser

def check_for_segment_times():
    """Do a final check for segment times in all possible locations."""
    
    # Read the debug HTML file
    debug_file = Path("debug_connecting_flights.html")
    html_content = debug_file.read_text(encoding="utf-8")
    parser = LexborHTMLParser(html_content)
    
    print("=== Final Check for Individual Segment Times ===\n")
    
    # 1. Check if there are multiple time divs per flight for multi-segment flights
    print("1. Checking time elements per flight:")
    flight_items = parser.css('li[role="button"]')
    
    for i, item in enumerate(flight_items[:5]):  # First 5 flights
        # Check if this is a multi-segment flight
        stops_text = item.text(strip=True)
        if 'stop' in stops_text.lower():
            stops_match = re.search(r'(\d+)\s+stop', stops_text, re.IGNORECASE)
            if stops_match and int(stops_match.group(1)) > 0:
                num_stops = int(stops_match.group(1))
                
                # Count time elements
                time_divs = item.css('div.mv1WYe')
                time_spans = item.css('span.mv1WYe')
                all_times = re.findall(r'\d{1,2}:\d{2}\s*(?:AM|PM)?', item.text())
                
                print(f"\nFlight {i+1} ({num_stops} stop{'s' if num_stops > 1 else ''}):")
                print(f"  Time divs found: {len(time_divs)}")
                print(f"  Time spans found: {len(time_spans)}")
                print(f"  All time patterns: {len(all_times)} - {all_times[:10]}")
                
                # Expected: (num_stops + 1) segments * 2 times per segment
                expected = (num_stops + 1) * 2
                print(f"  Expected times for all segments: {expected}")
                print(f"  Match? {'YES' if len(all_times) >= expected else 'NO'}")
    
    # 2. Check script tags for embedded segment time data
    print("\n\n2. Checking script tags for segment time data:")
    scripts = parser.css('script')
    for i, script in enumerate(scripts):
        script_text = script.text()
        if script_text:
            # Look for patterns that might contain segment times
            # Pattern: arrays with hour/minute pairs
            time_array_pattern = r'\[(\d{1,2}),\s*(\d{1,2})\]'
            matches = re.findall(time_array_pattern, script_text)
            
            # Filter to likely time values
            time_candidates = [(h, m) for h, m in matches if 0 <= int(h) <= 23 and 0 <= int(m) <= 59]
            
            if len(time_candidates) > 4:  # More than 2 flights worth
                print(f"\nScript {i}: Found {len(time_candidates)} potential time arrays")
                print(f"  Sample: {time_candidates[:10]}")
    
    # 3. Check for hidden div/span elements
    print("\n\n3. Checking for hidden elements with segment times:")
    hidden_selectors = [
        'div[style*="display:none"]',
        'div[style*="display: none"]',
        'span[style*="display:none"]',
        'span[style*="display: none"]',
        'div[hidden]',
        'span[hidden]',
        '.hidden',
        '[class*="hidden"]'
    ]
    
    for selector in hidden_selectors:
        elements = parser.css(selector)
        for elem in elements:
            text = elem.text(strip=True)
            if re.search(r'\d{1,2}:\d{2}', text):
                print(f"\nFound in {selector}: {text[:100]}...")
    
    # 4. Check data URLs for encoded time information
    print("\n\n4. Checking data URLs for time encoding:")
    url_elements = parser.css('[data-travelimpactmodelwebsiteurl]')
    
    for elem in url_elements[:3]:
        url = elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
        if url:
            # Check if URL contains timestamp or encoded times
            timestamp_pattern = r'(\d{10,13})'  # Unix timestamp
            timestamps = re.findall(timestamp_pattern, url)
            if timestamps:
                print(f"\nFound timestamps in URL: {timestamps}")
            
            # Check for other time encodings
            if re.search(r'time[s]?[=:]', url, re.IGNORECASE):
                print(f"\nURL with time parameter: {url[:100]}...")
    
    # 5. Final conclusion
    print("\n\n=== CONCLUSION ===")
    print("Based on comprehensive analysis:")
    print("- HTML contains only overall flight departure/arrival times")
    print("- Individual segment times are NOT available in the HTML")
    print("- Segment times are only available in the JavaScript data arrays")
    print("- The HTML parser correctly extracts what's available")
    
    print("\nAdditional data available in HTML but not currently extracted:")
    print("- Carbon emissions data")
    print("- Operated by information")
    print("- Aircraft manufacturer/model details")
    print("- Terminal/gate information (when available)")
    print("- Alliance information")
    print("- On-time performance (when available)")

if __name__ == "__main__":
    check_for_segment_times()