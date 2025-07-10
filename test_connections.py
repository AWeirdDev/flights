#!/usr/bin/env python3

import json
from pathlib import Path
from fast_flights.core import parse_response
from fast_flights.primp import Response
from fast_flights.schema import Layover


def test_debug_file():
    """Test parsing the debug_connecting_flights.html file"""
    
    # Read the debug HTML file
    debug_file = Path("debug_connecting_flights.html")
    if not debug_file.exists():
        print(f"Error: {debug_file} not found")
        return
    
    html_content = debug_file.read_text(encoding="utf-8")
    
    # Create a mock Response object
    class MockResponse:
        def __init__(self, text):
            self.text = text
            self.text_markdown = text
            self.status_code = 200
    
    response = MockResponse(html_content)
    
    # Test with JS data source
    print("Testing with JS data source...")
    try:
        result_js = parse_response(response, data_source='js')
        print(f"Found {len(result_js.flights)} flights using JS parser")
        
        # Print details of flights with connections
        for i, flight in enumerate(result_js.flights):
            if flight.connections:
                print(f"\nFlight {i+1} with connections:")
                print(f"  Route: {flight.departure_airport} → {flight.arrival_airport}")
                print(f"  Stops: {flight.stops}")
                print(f"  Price: ${flight.price}")
                print(f"  Connections ({len(flight.connections)}):")
                for j, conn in enumerate(flight.connections):
                    if isinstance(conn, Layover):
                        # This is a Layover
                        print(f"    Layover: {conn.duration}")
                    else:
                        # This is a FlightSegment
                        print(f"    Segment: {conn.departure_airport} → {conn.arrival_airport}")
                        print(f"      Flight: {conn.flight_number}")
                        print(f"      Duration: {conn.duration}")
                        print(f"      Departure: {conn.departure}")
                        print(f"      Arrival: {conn.arrival}")
                    
    except Exception as e:
        print(f"Error with JS parser: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50 + "\n")
    
    # Test with HTML data source
    print("Testing with HTML data source...")
    try:
        result_html = parse_response(response, data_source='html')
        print(f"Found {len(result_html.flights)} flights using HTML parser")
        
        # Print details of flights with connections
        for i, flight in enumerate(result_html.flights):
            if flight.connections:
                print(f"\nFlight {i+1} with connections:")
                print(f"  Route: {flight.departure_airport} → {flight.arrival_airport}")
                print(f"  Stops: {flight.stops}")
                print(f"  Price: ${flight.price}")
                print(f"  Connections ({len(flight.connections)}):")
                for j, conn in enumerate(flight.connections):
                    if isinstance(conn, Layover):
                        # This is a Layover
                        print(f"    Layover: {conn.duration}")
                    else:
                        # This is a FlightSegment
                        print(f"    Segment: {conn.departure_airport} → {conn.arrival_airport}")
                        print(f"      Flight: {conn.flight_number}")
                    
    except Exception as e:
        print(f"Error with HTML parser: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_debug_file()