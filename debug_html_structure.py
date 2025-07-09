#!/usr/bin/env python3
"""
Debug script to explore the actual HTML structure from Bright Data
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

def explore_html_structure():
    """Explore the actual HTML structure to find where fields might be"""
    print("Exploring HTML Structure")
    print("=" * 50)
    
    # Use a simple domestic route
    filter = create_filter(
        flight_data=[FlightData(date="2025-08-15", from_airport="JFK", to_airport="LAX")],
        trip="one-way",
        passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
        seat="economy",
        max_stops=None,
    )
    
    # Get the raw HTML response
    data = filter.as_b64()
    params = {
        "tfs": data.decode("utf-8"),
        "hl": "en",
        "tfu": "EgQIABABIgA",
        "curr": "",
    }
    
    response = bright_data_fetch(params)
    parser = LexborHTMLParser(response.text)
    
    # Look for flight items
    flight_items = parser.css('ul.Rk10dc li')
    
    print(f"Found {len(flight_items)} flight items")
    
    if flight_items:
        print(f"\n--- Detailed analysis of first flight item ---")
        item = flight_items[0]
        
        # Show full HTML structure
        print(f"Full HTML of first item:")
        print("-" * 50)
        item_html = str(item)
        print(item_html[:2000])  # First 2000 chars
        print("..." if len(item_html) > 2000 else "")
        
        # Look for all spans in the item
        spans = item.css('span')
        print(f"\n--- Found {len(spans)} span elements ---")
        for i, span in enumerate(spans[:15]):  # Show first 15
            text = span.text(strip=True)
            classes = span.attributes.get('class', '')
            aria_label = span.attributes.get('aria-label', '')
            print(f"Span {i+1}: text='{text}' classes='{classes}' aria-label='{aria_label[:100]}...' " + 
                  f"({len(aria_label)} chars)" if aria_label else "")
        
        # Look for all divs in the item
        divs = item.css('div')
        print(f"\n--- Found {len(divs)} div elements ---")
        for i, div in enumerate(divs[:10]):  # Show first 10
            text = div.text(strip=True)
            classes = div.attributes.get('class', '')
            aria_label = div.attributes.get('aria-label', '')
            if text or classes or aria_label:
                print(f"Div {i+1}: text='{text[:50]}...' classes='{classes}' aria-label='{aria_label[:100]}...' " + 
                      f"({len(aria_label)} chars)" if aria_label else "")
        
        # Look for any elements with aria-label
        print(f"\n--- Elements with aria-label ---")
        aria_elements = item.css('[aria-label]')
        for i, elem in enumerate(aria_elements[:10]):
            aria_label = elem.attributes.get('aria-label', '')
            tag_name = elem.tag
            classes = elem.attributes.get('class', '')
            print(f"Element {i+1} ({tag_name}): classes='{classes}' aria-label='{aria_label[:200]}...' " + 
                  f"({len(aria_label)} chars)")
        
        # Search for specific keywords in all text
        print(f"\n--- Searching for keywords in all text ---")
        all_text = item.text()
        
        keywords = ['delay', 'operated by', 'terminal', 'alliance', 'on-time', 'star alliance', 'oneworld', 'skyteam']
        for keyword in keywords:
            if keyword.lower() in all_text.lower():
                print(f"✅ Found '{keyword}' in text")
                # Find the context
                text_lower = all_text.lower()
                pos = text_lower.find(keyword.lower())
                if pos != -1:
                    context = all_text[max(0, pos-50):pos+len(keyword)+50]
                    print(f"    Context: ...{context}...")
            else:
                print(f"❌ '{keyword}' not found")
        
        # Look for percentage signs (might indicate on-time performance)
        print(f"\n--- Text containing '%' ---")
        if '%' in all_text:
            lines_with_percent = [line.strip() for line in all_text.split('\n') if '%' in line]
            for line in lines_with_percent[:5]:
                print(f"  {line}")
        else:
            print("No '%' found in text")
        
        print(f"\n--- Summary ---")
        print(f"Total text length: {len(all_text)}")
        print(f"Total spans: {len(spans)}")
        print(f"Total divs: {len(divs)}")
        print(f"Elements with aria-label: {len(aria_elements)}")
        
        # Check if this is similar to the expected HTML structure
        print(f"\n--- HTML Structure Check ---")
        # Look for expected selectors used in the original HTML parser
        expected_selectors = [
            ".GsCCve",  # delay
            "span.bOzv6",  # time ahead
            ".YMlIz.FpEdX",  # price
            ".BbR8Ec .ogfYpf",  # stops
            "span.mv1WYe div",  # departure/arrival times
            ".sSHqwe.tPgKwe.ogfYpf span",  # flight name
        ]
        
        for selector in expected_selectors:
            elements = item.css(selector)
            if elements:
                print(f"✅ Found {len(elements)} elements with '{selector}'")
                if elements[0].text(strip=True):
                    print(f"    Text: '{elements[0].text(strip=True)}'")
            else:
                print(f"❌ No elements found with '{selector}'")

if __name__ == "__main__":
    explore_html_structure()