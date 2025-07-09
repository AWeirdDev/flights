#!/usr/bin/env python3
"""
Debug script to inspect HTML elements and aria-labels for field extraction
"""

import os
import re
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers
from fast_flights.bright_data_fetch import bright_data_fetch
from fast_flights.filter import TFSData
from selectolax.lexbor import LexborHTMLParser

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

def debug_html_extraction():
    """Debug HTML extraction for a single route"""
    print("Debug HTML Extraction")
    print("=" * 50)
    
    # Use a simple domestic route
    filter = create_filter(
        flight_data=[FlightData(date="2025-08-15", from_airport="JFK", to_airport="LAX")],
        trip="one-way",
        passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
        seat="economy",
        max_stops=None,
    )
    
    print("Fetching HTML content...")
    
    # Get the raw HTML response
    data = filter.as_b64()
    params = {
        "tfs": data.decode("utf-8"),
        "hl": "en",
        "tfu": "EgQIABABIgA",
        "curr": "",
    }
    
    # Fetch using Bright Data
    response = bright_data_fetch(params)
    
    print(f"Response status: {response.status_code}")
    print(f"Response length: {len(response.text)} characters")
    
    # Parse with selectolax
    parser = LexborHTMLParser(response.text)
    
    print("\n" + "=" * 50)
    print("FLIGHT ITEMS ANALYSIS")
    print("=" * 50)
    
    # Use the same container-based approach as the actual parsing logic
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    print(f"Found {len(flight_containers)} flight containers")
    
    all_flight_items = []
    for i, container in enumerate(flight_containers):
        items_in_container = container.css("ul.Rk10dc li")
        print(f"Container {i+1}: {len(items_in_container)} items")
        all_flight_items.extend(items_in_container)
    
    print(f"Total flight items: {len(all_flight_items)}")
    
    # Also try the old direct approach for comparison
    direct_flight_items = parser.css('ul.Rk10dc li')
    print(f"Direct approach found: {len(direct_flight_items)} items")
    
    # Compare approaches
    print(f"\n--- Comparing Approaches ---")
    if len(all_flight_items) == len(direct_flight_items):
        print("✅ Both approaches found the same number of items")
    else:
        print(f"❌ Different counts: container-based={len(all_flight_items)}, direct={len(direct_flight_items)}")
    
    # Use container-based items for analysis (since that's what the actual parser uses)
    flight_items = all_flight_items
    
    if not flight_items:
        print("❌ No flight items found! Checking selectors...")
        
        # Try to find any lists
        all_lists = parser.css('ul')
        print(f"Found {len(all_lists)} <ul> elements")
        
        all_divs = parser.css('div[jsname]')
        print(f"Found {len(all_divs)} <div> elements with jsname")
        
        for i, div in enumerate(all_divs[:5]):
            jsname = div.attributes.get('jsname', '')
            print(f"  Div {i+1}: jsname='{jsname}'")
        
        return
    
    print(f"\n--- Analyzing first 3 flight items ---")
    
    for i, item in enumerate(flight_items[:3]):
        print(f"\nFLIGHT ITEM {i+1}:")
        print("-" * 30)
        
        # Check aria-label
        aria_label = item.attributes.get('aria-label', '')
        print(f"Aria-label length: {len(aria_label)}")
        if aria_label:
            print(f"Aria-label (first 200 chars): {aria_label[:200]}...")
        else:
            print("❌ No aria-label found")
        
        # Check for specific field elements
        print(f"\nElement inspection:")
        
        # Delay element
        delay_elem = item.css_first(".GsCCve")
        if delay_elem:
            delay_text = delay_elem.text(strip=True)
            print(f"  ✅ Delay element found: '{delay_text}'")
        else:
            print(f"  ❌ Delay element (.GsCCve) not found")
        
        # Time ahead element
        time_ahead_elem = item.css_first("span.bOzv6")
        if time_ahead_elem:
            time_ahead_text = time_ahead_elem.text(strip=True)
            print(f"  ✅ Time ahead element found: '{time_ahead_text}'")
        else:
            print(f"  ❌ Time ahead element (span.bOzv6) not found")
        
        # Check for pattern matches in aria-label
        if aria_label:
            print(f"\nPattern matching in aria-label:")
            
            # Operated by
            operated_pattern = r'Operated by ([^.,]+)'
            operated_matches = re.findall(operated_pattern, aria_label)
            if operated_matches:
                print(f"  ✅ Operated by matches: {operated_matches}")
            else:
                print(f"  ❌ No 'Operated by' matches")
                # Check if "operated" appears at all
                if 'operated' in aria_label.lower():
                    print(f"    ('operated' found in aria-label)")
            
            # Terminal info
            terminal_pattern = r'Terminal\\s+([A-Z0-9]+)'
            terminal_matches = re.findall(terminal_pattern, aria_label)
            if terminal_matches:
                print(f"  ✅ Terminal matches: {terminal_matches}")
            else:
                print(f"  ❌ No 'Terminal' matches")
                if 'terminal' in aria_label.lower():
                    print(f"    ('terminal' found in aria-label)")
            
            # Alliance
            alliance_pattern = r'(Star Alliance|oneworld|SkyTeam)'
            alliance_match = re.search(alliance_pattern, aria_label)
            if alliance_match:
                print(f"  ✅ Alliance match: {alliance_match.group(1)}")
            else:
                print(f"  ❌ No alliance matches")
                if any(word in aria_label.lower() for word in ['alliance', 'star', 'oneworld', 'skyteam']):
                    print(f"    (alliance-related words found)")
            
            # On-time performance
            ontime_pattern = r'(\\d+)%\\s*on[\\s-]?time'
            ontime_match = re.search(ontime_pattern, aria_label, re.IGNORECASE)
            if ontime_match:
                print(f"  ✅ On-time performance match: {ontime_match.group(1)}%")
            else:
                print(f"  ❌ No on-time performance matches")
                if 'time' in aria_label.lower() and '%' in aria_label:
                    print(f"    (time and % found in aria-label)")
        
        # Show more detailed HTML structure
        print(f"\nHTML structure (first 800 chars):")
        item_html = str(item)[:800]
        print(f"  {item_html}...")
        
        print(f"\nCSS classes on this item:")
        classes = item.attributes.get('class', '').split()
        for cls in classes[:10]:
            print(f"  - {cls}")
        
        # Debug: Look for ANY elements with the expected selectors
        print(f"\nDebugging CSS selectors in this item:")
        
        # Look for any elements containing "delay" or similar
        delay_candidates = item.css('*')
        delay_found = False
        for elem in delay_candidates:
            text = elem.text(strip=True).lower()
            if 'delay' in text or 'late' in text:
                classes = elem.attributes.get('class', '')
                print(f"  Delay candidate: <{elem.tag}> class='{classes}' text='{text}'")
                delay_found = True
        if not delay_found:
            print("  No delay-related text found in any element")
        
        # Look for any spans (time ahead might be in a span)
        all_spans = item.css('span')
        print(f"  Found {len(all_spans)} <span> elements:")
        for j, span in enumerate(all_spans[:5]):
            classes = span.attributes.get('class', '')
            text = span.text(strip=True)
            print(f"    Span {j+1}: class='{classes}' text='{text}'")
        
        # Look for any elements with aria-label
        aria_elements = item.css('*[aria-label]')
        if aria_elements:
            print(f"  Found {len(aria_elements)} elements with aria-label:")
            for j, elem in enumerate(aria_elements[:3]):
                aria_label = elem.attributes.get('aria-label', '')
                tag = elem.tag
                classes = elem.attributes.get('class', '')
                print(f"    Element {j+1}: <{tag}> class='{classes}' aria-label='{aria_label[:100]}...'")
        else:
            print("  No elements with aria-label found in this item")
        
        # Focus on the JMc5Xc div which seems to contain the main flight info
        jmc5xc_div = item.css_first('div.JMc5Xc')
        if jmc5xc_div:
            full_aria_label = jmc5xc_div.attributes.get('aria-label', '')
            print(f"\n  FULL ARIA-LABEL from JMc5Xc div:")
            print(f"    {full_aria_label}")
            
            # Test the patterns from the hybrid approach
            print(f"\n  Testing extraction patterns:")
            
            # Operated by
            import re
            operated_pattern = r'Operated by ([^.,]+)'
            operated_matches = re.findall(operated_pattern, full_aria_label)
            if operated_matches:
                print(f"    ✅ Operated by: {operated_matches}")
            else:
                print(f"    ❌ No 'Operated by' matches")
            
            # Terminal info
            terminal_pattern = r'Terminal\s+([A-Z0-9]+)'
            terminal_matches = re.findall(terminal_pattern, full_aria_label)
            if terminal_matches:
                print(f"    ✅ Terminal: {terminal_matches}")
            else:
                print(f"    ❌ No 'Terminal' matches")
            
            # Alliance
            alliance_pattern = r'(Star Alliance|oneworld|SkyTeam)'
            alliance_match = re.search(alliance_pattern, full_aria_label)
            if alliance_match:
                print(f"    ✅ Alliance: {alliance_match.group(1)}")
            else:
                print(f"    ❌ No alliance matches")
            
            # On-time performance
            ontime_pattern = r'(\d+)%\s*on[\s-]?time'
            ontime_match = re.search(ontime_pattern, full_aria_label, re.IGNORECASE)
            if ontime_match:
                print(f"    ✅ On-time performance: {ontime_match.group(1)}%")
            else:
                print(f"    ❌ No on-time performance matches")
        else:
            print("  ❌ No JMc5Xc div found")

if __name__ == "__main__":
    debug_html_extraction()