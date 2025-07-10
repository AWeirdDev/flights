#!/usr/bin/env python3
"""
Test what fields the upstream/main branch can extract from downloaded HTML files
"""

import os
import glob
from selectolax.lexbor import LexborHTMLParser

def safe(node):
    """Safe node access helper"""
    class _blank:
        def text(self, *_, **__):
            return ""
        def iter(self):
            return []
    return node or _blank()

def extract_flights_upstream(html_content):
    """Extract flights using upstream/main logic"""
    parser = LexborHTMLParser(html_content)
    flights = []
    
    for i, fl in enumerate(parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')):
        is_best_flight = i == 0
        
        for item in fl.css("ul.Rk10dc li")[:-1]:  # Skip last item like upstream does
            flight_data = {}
            
            # Flight name
            name = safe(item.css_first("div.sSHqwe.tPgKwe.ogfYpf span")).text(strip=True)
            flight_data['name'] = name
            
            # Get departure & arrival time
            dp_ar_node = item.css("span.mv1WYe div")
            try:
                flight_data['departure_time'] = dp_ar_node[0].text(strip=True)
                flight_data['arrival_time'] = dp_ar_node[1].text(strip=True)
            except IndexError:
                flight_data['departure_time'] = ""
                flight_data['arrival_time'] = ""
            
            # Get arrival time ahead (THIS IS THE KEY DIFFERENCE!)
            time_ahead = safe(item.css_first("span.bOzv6")).text()
            flight_data['arrival_time_ahead'] = time_ahead
            
            # Get duration
            duration = safe(item.css_first("li div.Ak5kof div")).text()
            flight_data['duration'] = duration
            
            # Get flight stops
            stops = safe(item.css_first(".BbR8Ec .ogfYpf")).text()
            flight_data['stops'] = stops
            
            # Get delay (THIS SELECTOR DOESN'T WORK IN BRIGHT DATA)
            delay = safe(item.css_first(".GsCCve")).text() or None
            flight_data['delay'] = delay
            
            # Get prices
            price = safe(item.css_first(".YMlIz.FpEdX")).text() or "0"
            flight_data['price'] = price
            
            # Check if we have any data
            if name or flight_data['departure_time']:
                flights.append(flight_data)
    
    return flights

def analyze_field_coverage(flights):
    """Analyze which fields have data"""
    field_counts = {
        'name': 0,
        'departure_time': 0,
        'arrival_time': 0,
        'arrival_time_ahead': 0,
        'duration': 0,
        'stops': 0,
        'delay': 0,
        'price': 0
    }
    
    field_samples = {field: [] for field in field_counts}
    
    for flight in flights:
        for field in field_counts:
            if flight.get(field) and flight[field].strip():
                field_counts[field] += 1
                if len(field_samples[field]) < 3:
                    field_samples[field].append(flight[field])
    
    return field_counts, field_samples

def main():
    """Test upstream extraction on all HTML files"""
    print("TESTING UPSTREAM/MAIN BRANCH FIELD EXTRACTION")
    print("=" * 70)
    
    # Find HTML files
    html_files = glob.glob('extreme_html_*.html')
    if not html_files:
        html_files = glob.glob('raw_html_*.html')
    
    if not html_files:
        print("No HTML files found.")
        return
    
    print(f"Found {len(html_files)} HTML files to test\n")
    
    # Track overall statistics
    total_flights = 0
    global_field_counts = {
        'name': 0,
        'departure_time': 0,
        'arrival_time': 0,
        'arrival_time_ahead': 0,
        'duration': 0,
        'stops': 0,
        'delay': 0,
        'price': 0
    }
    files_with_time_ahead = 0
    files_with_delay = 0
    
    # Test first 10 files in detail
    for i, html_file in enumerate(html_files[:10]):
        print(f"\nFile {i+1}: {html_file}")
        print("-" * 50)
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        flights = extract_flights_upstream(html_content)
        field_counts, field_samples = analyze_field_coverage(flights)
        
        print(f"Flights extracted: {len(flights)}")
        total_flights += len(flights)
        
        # Update global counts
        for field in global_field_counts:
            global_field_counts[field] += field_counts[field]
            
        if field_counts['arrival_time_ahead'] > 0:
            files_with_time_ahead += 1
        if field_counts['delay'] > 0:
            files_with_delay += 1
        
        # Show field coverage
        print("\nField coverage:")
        for field, count in field_counts.items():
            if len(flights) > 0:
                percentage = (count / len(flights)) * 100
                print(f"  {field}: {count}/{len(flights)} ({percentage:.1f}%)")
                if field_samples[field] and field in ['arrival_time_ahead', 'delay']:
                    print(f"    Samples: {field_samples[field]}")
    
    # Overall summary
    print(f"\n{'='*70}")
    print("OVERALL SUMMARY")
    print(f"{'='*70}")
    print(f"Total flights extracted: {total_flights}")
    print(f"Files with arrival_time_ahead data: {files_with_time_ahead}/10")
    print(f"Files with delay data: {files_with_delay}/10")
    
    print("\nGlobal field coverage:")
    for field, count in global_field_counts.items():
        if total_flights > 0:
            percentage = (count / total_flights) * 100
            print(f"  {field}: {count}/{total_flights} ({percentage:.1f}%)")
    
    print(f"\n🔍 KEY FINDINGS:")
    if global_field_counts['arrival_time_ahead'] > 0:
        print(f"✅ ARRIVAL_TIME_AHEAD is extractable! Found in {files_with_time_ahead}/10 files")
        print("   The span.bOzv6 selector DOES work with Bright Data HTML")
    else:
        print("❌ ARRIVAL_TIME_AHEAD not found")
        
    if global_field_counts['delay'] > 0:
        print(f"✅ DELAY is extractable! Found in {files_with_delay}/10 files")
    else:
        print("❌ DELAY not found (GsCCve selector doesn't exist in Bright Data HTML)")

if __name__ == "__main__":
    main()