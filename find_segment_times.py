#!/usr/bin/env python3
"""
Search for individual flight segment times in the HTML.
Focus on multi-segment flights to find patterns.
"""

import re
from pathlib import Path
from selectolax.lexbor import LexborHTMLParser

def find_flight_containers(parser):
    """Find all flight containers and analyze their structure."""
    # Find flight list items
    flight_items = parser.css('li[role="button"]')
    
    multi_segment_flights = []
    
    for item in flight_items:
        # Check if this is a multi-segment flight
        text = item.text(strip=True)
        stops_match = re.search(r'(\d+)\s+stop', text, re.IGNORECASE)
        
        if stops_match and int(stops_match.group(1)) > 0:
            # This is a connecting flight
            aria_label = item.attributes.get('aria-label', '')
            
            # Look for all time patterns in this flight item
            all_times = re.findall(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)', text, re.IGNORECASE)
            
            # Get the data URL to identify segments
            url_elem = item.css_first('[data-travelimpactmodelwebsiteurl]')
            url = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '') if url_elem else ''
            
            # Extract flight numbers from URL
            segments = []
            if url:
                # Pattern: JFK-MCO-F9-4871-20250801,MCO-LAX-F9-4145-20250801
                route_match = re.search(r'itinerary=([^&]+)', url)
                if route_match:
                    segment_strings = route_match.group(1).split(',')
                    for seg in segment_strings:
                        parts = seg.split('-')
                        if len(parts) >= 4:
                            segments.append({
                                'from': parts[0],
                                'to': parts[1],
                                'airline': parts[2],
                                'number': parts[3]
                            })
            
            multi_segment_flights.append({
                'stops': int(stops_match.group(1)),
                'times_found': all_times,
                'aria_label': aria_label,
                'segments': segments,
                'full_text': text[:500]  # First 500 chars
            })
    
    return multi_segment_flights

def analyze_time_patterns(flights):
    """Analyze the time patterns found in multi-segment flights."""
    print("=== Analyzing Multi-Segment Flights ===\n")
    
    for i, flight in enumerate(flights[:5]):  # First 5 flights
        print(f"Flight {i+1} ({flight['stops']} stop{'s' if flight['stops'] > 1 else ''}):")
        print(f"  Segments: {len(flight['segments'])}")
        
        if flight['segments']:
            for j, seg in enumerate(flight['segments']):
                print(f"    {j+1}. {seg['from']} → {seg['to']} ({seg['airline']} {seg['number']})")
        
        print(f"  Times found in text: {flight['times_found']}")
        print(f"  Number of times: {len(flight['times_found'])}")
        
        # For a 1-stop flight, we expect 4 times: dep1, arr1, dep2, arr2
        # For a 2-stop flight, we expect 6 times: dep1, arr1, dep2, arr2, dep3, arr3
        expected_times = (flight['stops'] + 1) * 2
        print(f"  Expected times for segments: {expected_times}")
        
        if len(flight['times_found']) >= expected_times:
            print("  ✓ Potentially has all segment times!")
            # Try to match times to segments
            if len(flight['segments']) > 0:
                times_per_segment = 2
                for j, seg in enumerate(flight['segments']):
                    start_idx = j * times_per_segment
                    if start_idx + 1 < len(flight['times_found']):
                        print(f"    Segment {j+1} times: {flight['times_found'][start_idx]} → {flight['times_found'][start_idx + 1]}")
        
        print(f"\n  Aria label preview: {flight['aria_label'][:200]}...")
        print("\n" + "-"*60 + "\n")

def search_for_hidden_times(parser):
    """Search for times that might be hidden in tooltips or other attributes."""
    print("=== Searching for Hidden Time Data ===\n")
    
    # Look for elements with title attributes
    elements_with_title = parser.css('[title]')
    for elem in elements_with_title:
        title = elem.attributes.get('title', '')
        if re.search(r'\d{1,2}:\d{2}', title):
            print(f"Found time in title: {title}")
            
    # Look for data attributes that might contain times
    all_elements = parser.css('*')
    time_pattern = re.compile(r'\d{1,2}:\d{2}')
    
    for elem in all_elements[:1000]:  # First 1000 elements
        for attr, value in elem.attributes.items():
            if attr.startswith('data-') and value and time_pattern.search(value):
                if 'segment' in value.lower() or 'flight' in value.lower():
                    print(f"Found time in {attr}: {value[:100]}...")

def look_for_tooltip_elements(parser):
    """Look for tooltip or hover elements that might contain segment times."""
    print("\n=== Looking for Tooltip/Hover Elements ===\n")
    
    # Common patterns for tooltips
    tooltip_selectors = [
        '[role="tooltip"]',
        '.tooltip',
        '[data-tooltip]',
        '[aria-describedby]',
        'div[style*="display: none"]',
        'div[style*="visibility: hidden"]'
    ]
    
    for selector in tooltip_selectors:
        elements = parser.css(selector)
        for elem in elements:
            text = elem.text(strip=True)
            if text and re.search(r'\d{1,2}:\d{2}', text):
                print(f"Found in {selector}: {text[:200]}...")

def main():
    # Read the debug HTML file
    debug_file = Path("debug_connecting_flights.html")
    if not debug_file.exists():
        print(f"Error: {debug_file} not found")
        return
    
    html_content = debug_file.read_text(encoding="utf-8")
    parser = LexborHTMLParser(html_content)
    
    # Find and analyze multi-segment flights
    multi_segment_flights = find_flight_containers(parser)
    analyze_time_patterns(multi_segment_flights)
    
    # Search for hidden time data
    search_for_hidden_times(parser)
    look_for_tooltip_elements(parser)
    
    # Additional analysis: Check if times appear in sequence
    print("\n=== Checking Time Sequence in HTML ===\n")
    
    # Extract all times from the HTML in order
    all_times = re.findall(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)', html_content)
    print(f"Total times found in HTML: {len(all_times)}")
    print("First 20 times:", all_times[:20])

if __name__ == "__main__":
    main()