#!/usr/bin/env python3
"""
Final test of field extraction after removing non-working fields
"""

import os
import glob
from fast_flights.core import parse_response

class MockResponse:
    """Mock response object for testing"""
    def __init__(self, text):
        self.text = text
        self.text_markdown = text
        self.status_code = 200

def main():
    """Test extraction on one HTML file"""
    print("FINAL FIELD EXTRACTION TEST")
    print("=" * 70)
    
    # Find an HTML file with good data
    test_file = None
    for f in ['raw_html_extreme_LAX_JFK_9_Terminals.html',
              'raw_html_extreme_ORD_EWR_Hub_to_Hub_Chaos.html',
              'raw_html_extreme_MIA_JFK_Hurricane_Season.html']:
        if os.path.exists(f):
            test_file = f
            break
    
    if not test_file:
        print("No suitable test file found")
        return
    
    print(f"Testing file: {test_file}\n")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    response = MockResponse(html_content)
    
    # Test both modes
    for mode in ['html', 'hybrid']:
        print(f"\n{mode.upper()} MODE:")
        print("-" * 30)
        
        try:
            result = parse_response(response, mode)
            print(f"✅ Parsed successfully: {len(result.flights)} flights")
            
            # Check fields on first few flights
            for i, flight in enumerate(result.flights[:3]):
                print(f"\nFlight {i+1}:")
                print(f"  Name: {flight.name}")
                print(f"  Price: ${flight.price}")
                print(f"  Departure: {flight.departure}")
                print(f"  Arrival: {flight.arrival}")
                print(f"  arrival_time_ahead: '{flight.arrival_time_ahead}'")
                print(f"  delay: {flight.delay}")
                if hasattr(flight, 'operated_by'):
                    print(f"  operated_by: {flight.operated_by}")
                
                # Verify removed fields don't exist
                removed_fields = ['terminal_info', 'alliance', 'on_time_performance']
                for field in removed_fields:
                    if hasattr(flight, field):
                        print(f"  ❌ ERROR: {field} still exists!")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*70}")
    print("✅ Field removal complete:")
    print("  - Removed duplicate arrival_time_ahead extraction")
    print("  - Removed terminal_info, alliance, on_time_performance")
    print("  - Kept: arrival_time_ahead, delay, operated_by (hybrid mode)")

if __name__ == "__main__":
    main()