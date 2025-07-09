#!/usr/bin/env python3
"""
Comprehensive analysis script to find departure/arrival times for connections
in the debug_connecting_flights.html file.
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from selectolax.lexbor import LexborHTMLParser

def extract_times_from_text(text):
    """Extract all time patterns from text."""
    # Multiple time patterns to catch different formats
    time_patterns = [
        r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',  # 12:30 PM
        r'(\d{1,2}:\d{2})',  # 12:30
        r'(\d{1,2}[.:]\d{2}\s*[ap]\.?m\.?)',  # 12.30 p.m.
    ]
    
    times = []
    for pattern in time_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        times.extend(matches)
    return times

def analyze_aria_labels(parser):
    """Analyze all aria-label attributes for time information."""
    print("\n=== Analyzing aria-label attributes ===")
    elements_with_aria = parser.css('[aria-label]')
    
    for elem in elements_with_aria:
        aria_label = elem.attributes.get('aria-label', '')
        if 'flight' in aria_label.lower() or 'segment' in aria_label.lower() or 'connection' in aria_label.lower():
            times = extract_times_from_text(aria_label)
            if times:
                print(f"\nFound times in aria-label: {times}")
                print(f"Full text: {aria_label[:200]}...")

def analyze_javascript(html_content):
    """Extract and analyze JavaScript data for connection times."""
    print("\n=== Analyzing JavaScript data ===")
    
    # Look for script tags with flight data
    script_pattern = r'<script[^>]*class="ds:1"[^>]*>(.*?)</script>'
    script_matches = re.findall(script_pattern, html_content, re.DOTALL)
    
    if script_matches:
        for i, script in enumerate(script_matches):
            # Look for array data patterns
            data_pattern = r'data:\s*(\[.*?\])'
            data_match = re.search(data_pattern, script)
            if data_match:
                try:
                    # Try to parse the JSON data
                    data_str = data_match.group(1)
                    # Look for time-like patterns in the data
                    time_patterns = re.findall(r'\[(\d+),(\d+)\]', data_str)
                    if time_patterns:
                        print(f"\nFound potential time tuples in script {i}: {time_patterns[:10]}...")
                        
                    # Look for structured flight data
                    flight_pattern = r'"([A-Z]{2}\d{3,4})"'
                    flights = re.findall(flight_pattern, script)
                    if flights:
                        print(f"Found flight numbers: {flights}")
                except:
                    pass

def analyze_css_selectors(parser):
    """Analyze specific CSS selectors that might contain connection times."""
    print("\n=== Analyzing CSS selectors for connection data ===")
    
    selectors = [
        'div.mv1WYe',  # Time containers
        'span.mv1WYe',
        'div.G2WY5c',  # Departure info
        'div.c8rWCd',  # Arrival info
        'div.sSHqwe',  # Flight details
        'span.bOzv6',  # Time ahead
        '.BbR8Ec',  # Stops info
        'div[jsname="IWWDBc"]',  # Flight containers
        'div[jsname="YdtKid"]',
        'li[role="button"]',  # Flight list items
    ]
    
    for selector in selectors:
        elements = parser.css(selector)
        for elem in elements:
            text = elem.text(strip=True)
            if text:
                times = extract_times_from_text(text)
                if times and len(text) < 200:  # Only show short text snippets
                    print(f"\nSelector: {selector}")
                    print(f"Times found: {times}")
                    print(f"Context: {text}")

def analyze_data_attributes(parser):
    """Analyze data-* attributes for connection information."""
    print("\n=== Analyzing data-* attributes ===")
    
    # Look for elements with data attributes
    all_elements = parser.css('*[data-travelimpactmodelwebsiteurl], *[data-ved], *[data-hveid]')
    
    for elem in all_elements:
        for attr, value in elem.attributes.items():
            if attr.startswith('data-') and value:
                # Check if the value contains flight or time information
                if re.search(r'[A-Z]{3}-[A-Z]{3}|flight|segment|\d{1,2}:\d{2}', value, re.IGNORECASE):
                    print(f"\nAttribute: {attr}")
                    print(f"Value: {value[:200]}...")
                    
                    # Extract any times found
                    times = extract_times_from_text(value)
                    if times:
                        print(f"Times found: {times}")

def find_connection_containers(parser):
    """Find containers that specifically hold connection/segment information."""
    print("\n=== Looking for connection containers ===")
    
    # Look for elements that might contain individual flight segments
    potential_containers = parser.css('li[role="button"] div.sSHqwe')
    
    for container in potential_containers:
        parent_li = container.parent
        while parent_li and parent_li.tag != 'li':
            parent_li = parent_li.parent
            
        if parent_li:
            # Get all text within this flight item
            all_text = parent_li.text(strip=True)
            
            # Check if this looks like a multi-segment flight
            if 'stop' in all_text.lower() or '+' in all_text:
                print(f"\nMulti-segment flight found:")
                print(f"Full text: {all_text[:300]}...")
                
                # Look for nested time elements
                time_elements = parent_li.css('div.mv1WYe, span.mv1WYe')
                if time_elements:
                    print("Time elements found:")
                    for te in time_elements:
                        print(f"  - {te.text(strip=True)}")

def main():
    # Read the debug HTML file
    debug_file = Path("debug_connecting_flights.html")
    if not debug_file.exists():
        print(f"Error: {debug_file} not found")
        return
    
    html_content = debug_file.read_text(encoding="utf-8")
    parser = LexborHTMLParser(html_content)
    
    # Run all analyses
    analyze_aria_labels(parser)
    analyze_javascript(html_content)
    analyze_css_selectors(parser)
    analyze_data_attributes(parser)
    find_connection_containers(parser)
    
    # Additional specific searches
    print("\n=== Specific pattern searches ===")
    
    # Search for patterns like "Departs 7:55 AM" or "Arrives 10:30 PM"
    depart_arrive_pattern = r'(Depart[s]?|Arrive[s]?|Departure|Arrival)\s*:?\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)'
    matches = re.findall(depart_arrive_pattern, html_content, re.IGNORECASE)
    if matches:
        print(f"\nFound departure/arrival patterns: {matches[:10]}")
    
    # Search for flight segment patterns
    segment_pattern = r'Segment\s*\d+.*?(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)'
    segment_matches = re.findall(segment_pattern, html_content, re.IGNORECASE)
    if segment_matches:
        print(f"\nFound segment time patterns: {segment_matches}")
    
    # Look for JavaScript objects that might contain flight data
    js_object_pattern = r'\{[^{}]*"flight[^{}]*\}'
    js_matches = re.findall(js_object_pattern, html_content, re.IGNORECASE)
    if js_matches:
        print(f"\nFound {len(js_matches)} JavaScript objects with flight data")
        for match in js_matches[:3]:  # Show first 3
            print(f"  {match[:100]}...")

if __name__ == "__main__":
    main()