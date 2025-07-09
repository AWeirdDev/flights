#!/usr/bin/env python3

from fast_flights import FlightData, Passengers, get_flights
import re

def debug_html_structure():
    """Debug the HTML structure to find flight number selectors"""
    try:
        print("Debugging HTML structure for flight numbers...")
        
        # Get the raw HTML response
        from fast_flights.core import fetch, TFSData
        
        flight_data = [
            FlightData(
                date="2025-08-01",
                from_airport="JFK",
                to_airport="LAX"
            )
        ]
        
        passengers = Passengers(adults=1)
        
        filter_obj = TFSData.from_interface(
            flight_data=flight_data,
            trip="one-way",
            passengers=passengers,
            seat="economy",
        )
        
        data = filter_obj.as_b64()
        params = {
            "tfs": data.decode("utf-8"),
            "hl": "en",
            "tfu": "EgQIABABIgA",
            "curr": "",
        }
        
        response = fetch(params)
        
        # Save HTML to file for analysis
        with open("debug_flights.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print("HTML saved to debug_flights.html")
        
        # Look for potential flight number patterns in the HTML
        html = response.text
        
        # Search for common flight number patterns
        patterns = [
            r'([A-Z]{2,3}\s?\d{2,4})',  # AA123, DL567, etc.
            r'Flight\s+([A-Z0-9]{2,}\s?\d{2,4})',  # Flight AA123
            r'([A-Z]{2,3}\d{2,4})',  # AA1234 (no space)
        ]
        
        print("\nSearching for flight number patterns:")
        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                print(f"Pattern '{pattern}' found: {matches[:5]}")  # Show first 5 matches
        
        # Look for airline names and nearby text
        airline_patterns = [
            r'JetBlue[^<]*',
            r'American[^<]*',
            r'Delta[^<]*',
            r'United[^<]*',
            r'Southwest[^<]*',
        ]
        
        print("\nSearching for airline names and context:")
        for pattern in airline_patterns:
            matches = re.findall(pattern, html)
            if matches:
                print(f"Airline pattern '{pattern}' found: {matches[:3]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_html_structure() 