#!/usr/bin/env python3
"""Analyze structural relationships between JS and HTML flight data."""

import sys
import json
import re
from typing import Dict, List, Any
from selectolax.lexbor import LexborHTMLParser

# Add the project to path
sys.path.insert(0, '/Users/dave/Work/flights')

from fast_flights.core import extract_html_enrichments, convert_decoded_to_result
from fast_flights.decoder import ResultDecoder
from fast_flights.flights_impl import FlightData, Passengers
from fast_flights.filter import TFSData
from fast_flights.bright_data_fetch import bright_data_fetch


def analyze_js_structure(decoded_data) -> Dict[str, Any]:
    """Analyze the structure of JS decoded data."""
    analysis = {
        'best_flights': len(decoded_data.best),
        'other_flights': len(decoded_data.other),
        'flight_details': []
    }
    
    # Analyze each flight's structure
    for idx, itinerary in enumerate(decoded_data.best + decoded_data.other):
        flight_info = {
            'index': idx,
            'is_best': idx < len(decoded_data.best),
            'num_segments': len(itinerary.flights),
            'airlines': [f.airline for f in itinerary.flights],
            'flight_numbers': [f"{f.airline} {f.flight_number}" for f in itinerary.flights],
            'route': f"{itinerary.departure_airport}-{itinerary.arrival_airport}",
            'segments': []
        }
        
        # Analyze each segment
        for seg in itinerary.flights:
            flight_info['segments'].append({
                'airline': seg.airline,
                'flight_number': f"{seg.airline} {seg.flight_number}",
                'departure': seg.departure_airport,
                'arrival': seg.arrival_airport,
                'aircraft': getattr(seg, 'aircraft', None)
            })
        
        # Check for unique identifiers
        if hasattr(itinerary, 'id'):
            flight_info['id'] = itinerary.id
        if hasattr(itinerary, 'url'):
            flight_info['url'] = itinerary.url
            
        analysis['flight_details'].append(flight_info)
    
    return analysis


def analyze_html_structure(parser: LexborHTMLParser) -> Dict[str, Any]:
    """Analyze the structure of HTML flight data."""
    analysis = {
        'containers': [],
        'unique_attributes': set(),
        'flight_elements': []
    }
    
    # Analyze container structure
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    
    for cont_idx, container in enumerate(flight_containers):
        container_info = {
            'index': cont_idx,
            'jsname': container.attributes.get('jsname', ''),
            'num_flights': len(container.css("ul.Rk10dc li")),
            'attributes': list(container.attributes.keys())
        }
        analysis['containers'].append(container_info)
        
        # Analyze individual flight elements
        flight_items = container.css("ul.Rk10dc li")
        
        for item_idx, item in enumerate(flight_items):
            flight_elem_info = {
                'container_index': cont_idx,
                'item_index': item_idx,
                'attributes': {},
                'data_attributes': {},
                'aria_label': '',
                'nested_elements': []
            }
            
            # Collect all attributes
            for attr_name, attr_value in item.attributes.items():
                analysis['unique_attributes'].add(attr_name)
                flight_elem_info['attributes'][attr_name] = attr_value
                
                if attr_name.startswith('data-'):
                    flight_elem_info['data_attributes'][attr_name] = attr_value
                    
                if attr_name == 'aria-label':
                    flight_elem_info['aria_label'] = attr_value
            
            # Look for nested elements with identifiers
            nested_with_data = item.css('[data-travelimpactmodelwebsiteurl]')
            for nested in nested_with_data:
                flight_elem_info['nested_elements'].append({
                    'tag': nested.tag,
                    'data-travelimpactmodelwebsiteurl': nested.attributes.get('data-travelimpactmodelwebsiteurl', '')
                })
            
            # Check for any unique identifiers
            id_elem = item.css_first('[id]')
            if id_elem:
                flight_elem_info['element_id'] = id_elem.attributes.get('id', '')
                
            analysis['flight_elements'].append(flight_elem_info)
    
    return analysis


def find_matching_strategies(js_analysis: Dict, html_analysis: Dict) -> List[Dict]:
    """Find potential matching strategies between JS and HTML data."""
    strategies = []
    
    # Strategy 1: Check if HTML elements have unique IDs that correlate with JS
    html_has_ids = any(elem.get('element_id') for elem in html_analysis['flight_elements'])
    js_has_ids = any(flight.get('id') for flight in js_analysis['flight_details'])
    
    if html_has_ids and js_has_ids:
        strategies.append({
            'name': 'Unique ID matching',
            'reliability': 'High',
            'description': 'Match using unique element IDs'
        })
    
    # Strategy 2: URL-based matching (current approach)
    html_has_urls = any(elem['data_attributes'].get('data-travelimpactmodelwebsiteurl') 
                       for elem in html_analysis['flight_elements'])
    
    if html_has_urls:
        strategies.append({
            'name': 'URL pattern matching',
            'reliability': 'Medium-High',
            'description': 'Match using flight itinerary URLs',
            'notes': 'Current approach but can be improved'
        })
    
    # Strategy 3: Aria-label parsing
    has_aria_labels = any(elem['aria_label'] for elem in html_analysis['flight_elements'])
    
    if has_aria_labels:
        strategies.append({
            'name': 'Aria-label content matching',
            'reliability': 'Medium',
            'description': 'Parse aria-labels to extract flight details and match',
            'notes': 'Requires parsing natural language descriptions'
        })
    
    # Strategy 4: Container-based grouping
    if len(html_analysis['containers']) > 1:
        strategies.append({
            'name': 'Container-aware matching',
            'reliability': 'Medium',
            'description': 'Use container grouping (best vs other) to narrow search',
            'notes': f"Found {len(html_analysis['containers'])} containers"
        })
    
    # Strategy 5: Nested structure analysis
    nested_count = sum(len(elem['nested_elements']) for elem in html_analysis['flight_elements'])
    if nested_count > 0:
        strategies.append({
            'name': 'Nested element matching',
            'reliability': 'Medium-High',
            'description': 'Use nested elements with data attributes for matching',
            'notes': f"Found {nested_count} nested elements with data"
        })
    
    return strategies


def main():
    print("=== Analyzing Structure for Better Matching ===\n")
    
    # Define test flight parameters
    flight_data = [
        FlightData(
            date="2025-08-16",
            from_airport="LAX",
            to_airport="JFK"
        )
    ]
    
    passengers = Passengers(adults=1)
    
    filter_data = TFSData.from_interface(
        flight_data=flight_data,
        trip="one-way",
        passengers=passengers,
        seat="economy",
        max_stops=None
    )
    
    params = {
        "tfs": filter_data.as_b64().decode("utf-8"),
        "hl": "en",
        "tfu": "EgQIABABIgA",
        "curr": "",
    }
    
    res = bright_data_fetch(params)
    parser = LexborHTMLParser(res.text)
    
    # Extract and analyze JS data
    script = parser.css_first(r'script.ds\:1').text()
    match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script)
    data = json.loads(match.group(1))
    decoded = ResultDecoder.decode(data)
    
    print("1. Analyzing JS Data Structure...")
    js_analysis = analyze_js_structure(decoded)
    print(f"   - Best flights: {js_analysis['best_flights']}")
    print(f"   - Other flights: {js_analysis['other_flights']}")
    print(f"   - Total: {len(js_analysis['flight_details'])}")
    
    print("\n2. Analyzing HTML Structure...")
    html_analysis = analyze_html_structure(parser)
    print(f"   - Containers: {len(html_analysis['containers'])}")
    print(f"   - Unique attributes found: {sorted(html_analysis['unique_attributes'])}")
    print(f"   - Total flight elements: {len(html_analysis['flight_elements'])}")
    
    print("\n3. Potential Matching Strategies:")
    strategies = find_matching_strategies(js_analysis, html_analysis)
    for strategy in strategies:
        print(f"\n   {strategy['name']}:")
        print(f"   - Reliability: {strategy['reliability']}")
        print(f"   - Description: {strategy['description']}")
        if 'notes' in strategy:
            print(f"   - Notes: {strategy['notes']}")
    
    print("\n4. Deep Dive: Analyzing URL patterns...")
    # Look at URL patterns in detail
    url_patterns = []
    for elem in html_analysis['flight_elements'][:10]:  # First 10
        if 'data-travelimpactmodelwebsiteurl' in elem['data_attributes']:
            url = elem['data_attributes']['data-travelimpactmodelwebsiteurl']
            # Extract itinerary part
            itinerary_match = re.search(r'itinerary=([^&]+)', url)
            if itinerary_match:
                url_patterns.append(itinerary_match.group(1))
    
    print("   Sample URL patterns:")
    for i, pattern in enumerate(url_patterns[:5]):
        print(f"   {i}: {pattern}")
    
    print("\n5. Deep Dive: Container structure...")
    for cont in html_analysis['containers']:
        print(f"   Container {cont['index']}: jsname='{cont['jsname']}', flights={cont['num_flights']}")
    
    print("\n6. Examining specific flight element structure...")
    # Look at first flight in detail
    if html_analysis['flight_elements']:
        first_flight = html_analysis['flight_elements'][0]
        print(f"   First flight element:")
        print(f"   - Container: {first_flight['container_index']}")
        print(f"   - Attributes: {list(first_flight['attributes'].keys())}")
        print(f"   - Data attributes: {first_flight['data_attributes']}")
        print(f"   - Nested elements with data: {len(first_flight['nested_elements'])}")
        
        if first_flight['aria_label']:
            print(f"   - Aria label preview: {first_flight['aria_label'][:100]}...")
    
    print("\n7. Recommendations:")
    print("   The most robust approach would be:")
    print("   1. Use container grouping to separate 'best' vs 'other' flights")
    print("   2. Within each group, use URL pattern matching as primary key")
    print("   3. For connecting flights, match on departure airport + first flight number")
    print("   4. Use aria-label parsing as fallback for validation")
    print("   5. Avoid index-based matching entirely")


if __name__ == "__main__":
    main()