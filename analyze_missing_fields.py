#!/usr/bin/env python3
"""
Analyze what additional fields we could extract from the flight data.
"""

from pathlib import Path
from fast_flights.core import parse_response
from selectolax.lexbor import LexborHTMLParser
import re
import json

def analyze_current_extraction():
    """See what we're currently extracting vs what's available."""
    
    # Read the debug HTML file
    debug_file = Path("debug_connecting_flights.html")
    html_content = debug_file.read_text(encoding="utf-8")
    
    class MockResponse:
        def __init__(self, text):
            self.text = text
            self.text_markdown = text
            self.status_code = 200
    
    response = MockResponse(html_content)
    
    # Parse with both sources
    try:
        result_js = parse_response(response, data_source='js')
        print("=== JS Parser Results ===")
        flight = result_js.flights[0]  # First flight
        print(f"Fields extracted:")
        for field, value in flight.__dict__.items():
            print(f"  {field}: {value}")
    except Exception as e:
        print(f"JS parser error: {e}")
    
    try:
        result_html = parse_response(response, data_source='html')
        print("\n=== HTML Parser Results ===")
        flight = result_html.flights[0]  # First flight
        print(f"Fields extracted:")
        for field, value in flight.__dict__.items():
            print(f"  {field}: {value}")
    except Exception as e:
        print(f"HTML parser error: {e}")
    
    # Now analyze what additional data might be available
    parser = LexborHTMLParser(html_content)
    
    print("\n=== Additional Data Available in HTML ===")
    
    # Look for emissions data
    emissions_elements = parser.css('[aria-label*="emission"], [aria-label*="CO2"], [aria-label*="carbon"]')
    if emissions_elements:
        print("\nEmissions data found:")
        for elem in emissions_elements[:3]:
            print(f"  {elem.attributes.get('aria-label', '')[:100]}...")
    
    # Look for baggage info
    baggage_elements = parser.css('[aria-label*="bag"], [aria-label*="luggage"]')
    if baggage_elements:
        print("\nBaggage info found:")
        for elem in baggage_elements[:3]:
            print(f"  {elem.attributes.get('aria-label', '')[:100]}...")
    
    # Look for seat/class info
    seat_elements = parser.css('[aria-label*="seat"], [aria-label*="class"], [aria-label*="cabin"]')
    if seat_elements:
        print("\nSeat/Class info found:")
        for elem in seat_elements[:3]:
            print(f"  {elem.attributes.get('aria-label', '')[:100]}...")
    
    # Look for operated by info
    operated_pattern = r'Operated by ([^.,]+)'
    operated_matches = re.findall(operated_pattern, html_content)
    if operated_matches:
        print(f"\nOperated by info found: {list(set(operated_matches))[:5]}")
    
    # Look for booking codes
    booking_pattern = r'booking\s*code[s]?\s*[:=]\s*([A-Z])'
    booking_matches = re.findall(booking_pattern, html_content, re.IGNORECASE)
    if booking_matches:
        print(f"\nBooking codes found: {booking_matches}")
    
    # Look for fare types
    fare_pattern = r'(Basic Economy|Main Cabin|Premium Economy|Business|First)\s*(Class)?'
    fare_matches = re.findall(fare_pattern, html_content)
    if fare_matches:
        print(f"\nFare types found: {list(set([m[0] for m in fare_matches]))}")
    
    # Look for alliance info
    alliance_pattern = r'(Star Alliance|oneworld|SkyTeam)'
    alliance_matches = re.findall(alliance_pattern, html_content)
    if alliance_matches:
        print(f"\nAlliance info found: {list(set(alliance_matches))}")
    
    # Look for meal service
    meal_pattern = r'(meal|snack|beverage|food)\s*(service|included)?'
    meal_matches = re.findall(meal_pattern, html_content, re.IGNORECASE)
    if meal_matches:
        print(f"\nMeal service info found: {len(meal_matches)} mentions")
    
    # Look for WiFi info
    wifi_pattern = r'(wifi|wi-fi|internet)\s*(available|included)?'
    wifi_matches = re.findall(wifi_pattern, html_content, re.IGNORECASE)
    if wifi_matches:
        print(f"\nWiFi info found: {len(wifi_matches)} mentions")
    
    # Look for terminal/gate info
    terminal_pattern = r'Terminal\s+([A-Z0-9]+)'
    gate_pattern = r'Gate\s+([A-Z0-9]+)'
    terminal_matches = re.findall(terminal_pattern, html_content)
    gate_matches = re.findall(gate_pattern, html_content)
    if terminal_matches:
        print(f"\nTerminal info found: {list(set(terminal_matches))[:5]}")
    if gate_matches:
        print(f"\nGate info found: {list(set(gate_matches))[:5]}")
    
    # Look for on-time performance
    ontime_pattern = r'(\d+)%\s*on[\s-]?time'
    ontime_matches = re.findall(ontime_pattern, html_content, re.IGNORECASE)
    if ontime_matches:
        print(f"\nOn-time performance found: {ontime_matches[:3]}")
    
    # Look for aircraft details beyond type
    aircraft_pattern = r'(Boeing|Airbus|Embraer|Bombardier)\s+([A-Z0-9-]+)'
    aircraft_matches = re.findall(aircraft_pattern, html_content)
    if aircraft_matches:
        print(f"\nDetailed aircraft info: {list(set(aircraft_matches))[:5]}")

if __name__ == "__main__":
    analyze_current_extraction()