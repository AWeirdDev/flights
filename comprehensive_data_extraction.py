#!/usr/bin/env python3
"""
Comprehensive analysis to extract ALL possible flight data from debug_connecting_flights.html
by combining JS, HTML, and CSS parsing.
"""

import re
import json
from pathlib import Path
from selectolax.lexbor import LexborHTMLParser
from collections import defaultdict

def extract_js_data(html_content):
    """Extract and parse JavaScript data."""
    script_pattern = r'<script[^>]*class="ds:1"[^>]*>(.*?)</script>'
    script_match = re.search(script_pattern, html_content, re.DOTALL)
    
    if not script_match:
        return None
        
    script_content = script_match.group(1)
    data_pattern = r'data:\s*(\[.*?\])(?=,|\s*\})'
    data_match = re.search(data_pattern, script_content, re.DOTALL)
    
    if not data_match:
        return None
        
    try:
        data_str = data_match.group(1)
        data = json.loads(data_str)
        return data
    except:
        return None

def extract_flight_details_from_js(data):
    """Extract detailed flight information from JS data structure."""
    flights = []
    
    # Process best and other flights
    categories = [('best', data[2][0] if len(data) > 2 and data[2] else []),
                  ('other', data[3][0] if len(data) > 3 and data[3] else [])]
    
    for category, itineraries in categories:
        for itinerary in itineraries:
            if not isinstance(itinerary, list) or not itinerary:
                continue
                
            flight_info = {
                'category': category,
                'segments': [],
                'layovers': [],
                'additional_data': {}
            }
            
            # Extract flight segments
            if (len(itinerary[0]) > 2 and isinstance(itinerary[0][2], list)):
                for segment in itinerary[0][2]:
                    if isinstance(segment, list) and len(segment) > 21:
                        seg_info = {
                            'departure_airport': segment[3] if len(segment) > 3 else None,
                            'departure_airport_name': segment[4] if len(segment) > 4 else None,
                            'arrival_airport': segment[5] if len(segment) > 5 else None,
                            'arrival_airport_name': segment[6] if len(segment) > 6 else None,
                            'departure_time': segment[8] if len(segment) > 8 else None,
                            'arrival_time': segment[10] if len(segment) > 10 else None,
                            'travel_time': segment[11] if len(segment) > 11 else None,
                            'aircraft': segment[17] if len(segment) > 17 else None,
                            'seat_pitch': segment[14] if len(segment) > 14 else None,
                            'departure_date': segment[20] if len(segment) > 20 else None,
                            'arrival_date': segment[21] if len(segment) > 21 else None,
                        }
                        
                        # Extract airline info
                        if len(segment) > 22 and isinstance(segment[22], list):
                            seg_info['airline_code'] = segment[22][0] if len(segment[22]) > 0 else None
                            seg_info['flight_number'] = segment[22][1] if len(segment[22]) > 1 else None
                            seg_info['airline_name'] = segment[22][3] if len(segment[22]) > 3 else None
                        
                        # Check for codeshares
                        if len(segment) > 15 and isinstance(segment[15], list):
                            seg_info['codeshares'] = []
                            for cs in segment[15]:
                                if isinstance(cs, list) and len(cs) > 3:
                                    seg_info['codeshares'].append({
                                        'airline': cs[0],
                                        'flight_number': cs[1],
                                        'airline_name': cs[3] if isinstance(cs[3], list) and cs[3] else None
                                    })
                        
                        flight_info['segments'].append(seg_info)
            
            # Extract layover information
            if (len(itinerary[0]) > 13 and isinstance(itinerary[0][13], list)):
                for layover in itinerary[0][13]:
                    if isinstance(layover, list) and len(layover) > 7:
                        flight_info['layovers'].append({
                            'duration_minutes': layover[0],
                            'departure_airport': layover[1] if len(layover) > 1 else None,
                            'departure_airport_name': layover[4] if len(layover) > 4 else None,
                            'departure_airport_city': layover[5] if len(layover) > 5 else None,
                            'arrival_airport': layover[2] if len(layover) > 2 else None,
                            'arrival_airport_name': layover[6] if len(layover) > 6 else None,
                            'arrival_airport_city': layover[7] if len(layover) > 7 else None,
                        })
            
            # Extract overall itinerary info
            if len(itinerary[0]) > 9:
                flight_info['overall'] = {
                    'departure_airport': itinerary[0][3] if len(itinerary[0]) > 3 else None,
                    'arrival_airport': itinerary[0][6] if len(itinerary[0]) > 6 else None,
                    'departure_time': itinerary[0][5] if len(itinerary[0]) > 5 else None,
                    'arrival_time': itinerary[0][8] if len(itinerary[0]) > 8 else None,
                    'total_travel_time': itinerary[0][9] if len(itinerary[0]) > 9 else None,
                    'departure_date': itinerary[0][4] if len(itinerary[0]) > 4 else None,
                    'arrival_date': itinerary[0][7] if len(itinerary[0]) > 7 else None,
                }
            
            # Extract price from protobuf
            if len(itinerary) > 1 and isinstance(itinerary[1], list) and len(itinerary[1]) > 1:
                # This would need protobuf decoding, but we can note it exists
                flight_info['has_price_data'] = True
            
            flights.append(flight_info)
    
    return flights

def extract_html_enrichments(parser):
    """Extract additional data from HTML that might not be in JS."""
    enrichments = []
    
    flight_items = parser.css('li[role="button"]')
    
    for item in flight_items:
        enrichment = {
            'aria_label': item.attributes.get('aria-label', ''),
            'additional_info': {}
        }
        
        # Extract detailed layover information from aria-label
        aria_label = enrichment['aria_label']
        if aria_label:
            # Extract terminal/gate info if present
            terminal_pattern = r'Terminal\s+([A-Z0-9]+)'
            terminal_matches = re.findall(terminal_pattern, aria_label)
            if terminal_matches:
                enrichment['additional_info']['terminals'] = terminal_matches
            
            # Extract gate info if present
            gate_pattern = r'Gate\s+([A-Z0-9]+)'
            gate_matches = re.findall(gate_pattern, aria_label)
            if gate_matches:
                enrichment['additional_info']['gates'] = gate_matches
            
            # Extract detailed layover descriptions
            layover_pattern = r'Layover \((\d+) of (\d+)\) is a ((?:\d+ hr )?(?:\d+ min)?) layover at ([^.]+)'
            layover_matches = re.findall(layover_pattern, aria_label)
            if layover_matches:
                enrichment['layover_details'] = [
                    {
                        'index': int(m[0]),
                        'total': int(m[1]),
                        'duration': m[2],
                        'airport_description': m[3].strip()
                    }
                    for m in layover_matches
                ]
            
            # Extract carrier-operated info
            operated_pattern = r'Operated by ([^.]+)'
            operated_matches = re.findall(operated_pattern, aria_label)
            if operated_matches:
                enrichment['additional_info']['operated_by'] = operated_matches
        
        # Look for emissions data
        emissions_elem = item.css_first('[aria-label*="emissions"]')
        if emissions_elem:
            enrichment['additional_info']['emissions_info'] = emissions_elem.attributes.get('aria-label', '')
        
        # Look for baggage info
        baggage_elem = item.css_first('[aria-label*="baggage"], [aria-label*="bag"]')
        if baggage_elem:
            enrichment['additional_info']['baggage_info'] = baggage_elem.attributes.get('aria-label', '')
        
        # Extract any warnings or notices
        warning_elems = item.css('.GsCCve, [role="alert"]')
        if warning_elems:
            enrichment['warnings'] = [elem.text(strip=True) for elem in warning_elems if elem.text(strip=True)]
        
        # Look for overnight indicators
        overnight_elem = item.css_first('.bOzv6')
        if overnight_elem:
            overnight_text = overnight_elem.text(strip=True)
            if '+' in overnight_text:
                enrichment['additional_info']['arrives_days_later'] = overnight_text
        
        # Extract booking class / fare info if present
        fare_elems = item.css('[aria-label*="fare"], [aria-label*="class"]')
        if fare_elems:
            enrichment['fare_info'] = [elem.attributes.get('aria-label', '') for elem in fare_elems]
        
        enrichments.append(enrichment)
    
    return enrichments

def find_additional_data_sources(parser, html_content):
    """Look for any other data sources in the HTML."""
    additional_data = {}
    
    # Look for JSON-LD structured data
    json_ld_scripts = parser.css('script[type="application/ld+json"]')
    if json_ld_scripts:
        additional_data['json_ld'] = []
        for script in json_ld_scripts:
            try:
                data = json.loads(script.text())
                additional_data['json_ld'].append(data)
            except:
                pass
    
    # Look for meta tags with flight info
    meta_tags = parser.css('meta[property*="flight"], meta[name*="flight"]')
    if meta_tags:
        additional_data['meta_tags'] = {
            tag.attributes.get('property') or tag.attributes.get('name'): tag.attributes.get('content')
            for tag in meta_tags
        }
    
    # Look for data attributes with additional info
    data_attrs = defaultdict(list)
    for elem in parser.css('*[data-ved], *[data-hveid]'):
        for attr, value in elem.attributes.items():
            if attr.startswith('data-') and 'flight' in str(value).lower():
                data_attrs[attr].append(value)
    
    if data_attrs:
        additional_data['data_attributes'] = dict(data_attrs)
    
    # Search for price details in script tags
    price_pattern = r'"price":\s*(\d+)'
    price_matches = re.findall(price_pattern, html_content)
    if price_matches:
        additional_data['price_values'] = list(set(price_matches))
    
    # Look for currency information
    currency_pattern = r'"currency":\s*"([A-Z]{3})"'
    currency_matches = re.findall(currency_pattern, html_content)
    if currency_matches:
        additional_data['currencies'] = list(set(currency_matches))
    
    return additional_data

def main():
    # Read the debug HTML file
    debug_file = Path("debug_connecting_flights.html")
    if not debug_file.exists():
        print(f"Error: {debug_file} not found")
        return
    
    html_content = debug_file.read_text(encoding="utf-8")
    parser = LexborHTMLParser(html_content)
    
    print("=== Comprehensive Flight Data Extraction ===\n")
    
    # 1. Extract JS data
    print("1. Extracting JavaScript data...")
    js_data = extract_js_data(html_content)
    if js_data:
        flights_from_js = extract_flight_details_from_js(js_data)
        print(f"   Found {len(flights_from_js)} flights in JS data")
        
        # Show sample of first flight with connections
        for flight in flights_from_js[:1]:
            if len(flight['segments']) > 1:
                print("\n   Sample multi-segment flight from JS:")
                print(f"   Category: {flight['category']}")
                print(f"   Segments: {len(flight['segments'])}")
                for i, seg in enumerate(flight['segments']):
                    print(f"\n   Segment {i+1}:")
                    print(f"     {seg['departure_airport']} → {seg['arrival_airport']}")
                    print(f"     Time: {seg['departure_time']} → {seg['arrival_time']}")
                    print(f"     Aircraft: {seg['aircraft']}")
                    print(f"     Airline: {seg.get('airline_name', 'N/A')}")
                    if seg.get('codeshares'):
                        print(f"     Codeshares: {len(seg['codeshares'])}")
    
    # 2. Extract HTML enrichments
    print("\n2. Extracting HTML enrichments...")
    html_enrichments = extract_html_enrichments(parser)
    print(f"   Found {len(html_enrichments)} flight items with enrichments")
    
    # Show sample enrichments
    for enrich in html_enrichments[:1]:
        if enrich.get('layover_details'):
            print("\n   Sample enrichment data:")
            print(f"   Layover details: {enrich['layover_details']}")
        if enrich.get('additional_info'):
            print(f"   Additional info: {enrich['additional_info']}")
    
    # 3. Find additional data sources
    print("\n3. Looking for additional data sources...")
    additional = find_additional_data_sources(parser, html_content)
    for key, value in additional.items():
        if value:
            print(f"   Found {key}: {len(value) if isinstance(value, list) else 'yes'}")
    
    # Summary of all available data fields
    print("\n=== Summary of All Available Data Fields ===")
    print("\nFrom JavaScript:")
    print("- Individual segment departure/arrival times")
    print("- Individual segment airports and cities") 
    print("- Aircraft types for each segment")
    print("- Seat pitch information")
    print("- Codeshare flight numbers")
    print("- Exact layover durations in minutes")
    print("- Departure/arrival dates")
    print("- Travel time for each segment")
    
    print("\nFrom HTML:")
    print("- Detailed layover descriptions with airport names")
    print("- Terminal information (if available)")
    print("- Gate information (if available)")
    print("- Operated by information")
    print("- Emissions data")
    print("- Baggage information")
    print("- Warnings and delays")
    print("- Days ahead indicators (+1, +2)")
    print("- Fare class information")
    
    print("\nFrom Other Sources:")
    for key in additional.keys():
        if additional[key]:
            print(f"- {key}")

if __name__ == "__main__":
    main()