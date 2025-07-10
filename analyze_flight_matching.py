#!/usr/bin/env python3
"""
Analyze HTML flight data to find reliable ways to match JS data with HTML enrichments
without using index-based matching.
"""

import re
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any
from selectolax.lexbor import LexborHTMLParser

def extract_flight_identifiers_from_url(url: str) -> Dict[str, Any]:
    """Extract flight identifiers from data-travelimpactmodelwebsiteurl."""
    if not url:
        return {}
    
    result = {
        'url': url,
        'segments': []
    }
    
    # Pattern: itinerary=JFK-LAX-F9-2503-20250801 or itinerary=JFK-MCO-F9-4871-20250801,MCO-LAX-F9-4145-20250801
    itinerary_match = re.search(r'itinerary=([A-Z0-9,-]+)', url)
    if itinerary_match:
        itinerary = itinerary_match.group(1)
        segments = itinerary.split(',')
        
        for segment in segments:
            parts = segment.split('-')
            if len(parts) >= 5:  # e.g., JFK-MCO-F9-4871-20250801
                seg_info = {
                    'departure_airport': parts[0],
                    'arrival_airport': parts[1],
                    'airline_code': parts[2],
                    'flight_number': parts[3],
                    'date': parts[4],
                    'full_flight_number': f"{parts[2]} {parts[3]}"
                }
                result['segments'].append(seg_info)
        
        # Overall route info
        if result['segments']:
            result['departure_airport'] = result['segments'][0]['departure_airport']
            result['arrival_airport'] = result['segments'][-1]['arrival_airport']
            result['is_direct'] = len(result['segments']) == 1
            result['connecting_airports'] = [seg['arrival_airport'] for seg in result['segments'][:-1]]
    
    return result

def extract_aria_label_info(aria_label: str) -> Dict[str, Any]:
    """Extract structured information from aria-label."""
    if not aria_label:
        return {}
    
    info = {
        'aria_label': aria_label,
        'price': None,
        'airline': None,
        'departure_time': None,
        'arrival_time': None,
        'duration': None,
        'stops': None,
        'operated_by': [],
        'flight_type': None
    }
    
    # Price extraction: "From 154 US dollars"
    price_match = re.search(r'From (\d+) (?:US )?dollar', aria_label)
    if price_match:
        info['price'] = int(price_match.group(1))
    
    # Flight type: "Nonstop flight" or "1 stop flight"
    if "Nonstop flight" in aria_label:
        info['flight_type'] = 'nonstop'
        info['stops'] = 0
    else:
        stops_match = re.search(r'(\d+) stop', aria_label)
        if stops_match:
            info['stops'] = int(stops_match.group(1))
            info['flight_type'] = 'connecting'
    
    # Airline extraction
    airline_match = re.search(r'flight with ([^.]+?)\.', aria_label)
    if airline_match:
        info['airline'] = airline_match.group(1).strip()
    
    # Time extraction
    time_pattern = r'at (\d+:\d+ [AP]M)'
    times = re.findall(time_pattern, aria_label)
    if len(times) >= 2:
        info['departure_time'] = times[0]
        info['arrival_time'] = times[1]
    
    # Duration extraction
    duration_match = re.search(r'Total duration ((?:\d+ hr )?(?:\d+ min)?)', aria_label)
    if duration_match:
        info['duration'] = duration_match.group(1).strip()
    
    # Operated by extraction
    operated_pattern = r'Operated by ([^.,]+)'
    operated_matches = re.findall(operated_pattern, aria_label)
    if operated_matches:
        info['operated_by'] = list(set(operated_matches))
    
    # Layover information
    layover_pattern = r'Layover \((\d+) of \d+\) is a ((?:\d+ hr )?(?:\d+ min)?) layover at ([^.]+)'
    layover_matches = re.findall(layover_pattern, aria_label)
    if layover_matches:
        info['layovers'] = []
        for idx, duration, airport in layover_matches:
            info['layovers'].append({
                'index': int(idx),
                'duration': duration,
                'airport': airport.strip()
            })
    
    return info

def find_flight_elements(html_content: str) -> List[Dict[str, Any]]:
    """Find all flight elements and extract their identifiers."""
    parser = LexborHTMLParser(html_content)
    flights = []
    
    # Find all elements with data-travelimpactmodelwebsiteurl
    url_elements = parser.css('[data-travelimpactmodelwebsiteurl]')
    url_to_element = {}
    
    for elem in url_elements:
        url = elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
        if url and url not in url_to_element:
            url_to_element[url] = elem
    
    # Find flight list items
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    
    for container_idx, container in enumerate(flight_containers):
        flight_items = container.css("ul.Rk10dc li")
        
        for item_idx, item in enumerate(flight_items):
            flight_info = {
                'container_index': container_idx,
                'item_index': item_idx,
                'data_attributes': {},
                'aria_labels': [],
                'urls': [],
                'element_hierarchy': []
            }
            
            # Get all data attributes on this element and its children
            all_elements = [item] + item.css('*')
            
            for elem in all_elements:
                # Collect data attributes
                for attr_name, attr_value in elem.attributes.items():
                    if attr_name.startswith('data-'):
                        if attr_name not in flight_info['data_attributes']:
                            flight_info['data_attributes'][attr_name] = []
                        flight_info['data_attributes'][attr_name].append(attr_value)
                
                # Collect aria-labels
                if 'aria-label' in elem.attributes:
                    aria_label = elem.attributes['aria-label']
                    if aria_label and 'flight' in aria_label.lower():
                        flight_info['aria_labels'].append({
                            'label': aria_label,
                            'tag': elem.tag,
                            'classes': elem.attributes.get('class', ''),
                            'parsed': extract_aria_label_info(aria_label)
                        })
                
                # Collect URLs
                if 'data-travelimpactmodelwebsiteurl' in elem.attributes:
                    url = elem.attributes['data-travelimpactmodelwebsiteurl']
                    url_info = extract_flight_identifiers_from_url(url)
                    flight_info['urls'].append({
                        'url': url,
                        'parsed': url_info,
                        'tag': elem.tag,
                        'classes': elem.attributes.get('class', '')
                    })
            
            # Build element hierarchy
            current = item
            hierarchy = []
            while current:
                hierarchy.append({
                    'tag': current.tag,
                    'classes': current.attributes.get('class', ''),
                    'jsname': current.attributes.get('jsname', ''),
                    'jscontroller': current.attributes.get('jscontroller', '')
                })
                current = current.parent
                if current and current.tag == 'body':
                    break
            
            flight_info['element_hierarchy'] = hierarchy[:5]  # Keep top 5 levels
            flights.append(flight_info)
    
    return flights

def analyze_js_data_structure(html_content: str) -> Dict[str, Any]:
    """Extract and analyze JavaScript data structure."""
    parser = LexborHTMLParser(html_content)
    js_analysis = {
        'found': False,
        'structure': None,
        'flight_count': 0,
        'sample_flights': []
    }
    
    # Find the script with flight data
    script_elem = parser.css_first(r'script.ds\:1')
    if not script_elem:
        return js_analysis
    
    script_text = script_elem.text()
    
    # Extract the data array
    match = re.search(r'data:(\[.*?\])(?:,|}).*?sideChannel', script_text, re.DOTALL)
    if not match:
        return js_analysis
    
    try:
        # Clean up the data string
        data_str = match.group(1)
        # Handle escaped quotes
        data_str = data_str.replace(r'\"', '"')
        
        # Parse JSON
        data = json.loads(data_str)
        js_analysis['found'] = True
        
        # Analyze structure
        if data and len(data) > 0 and isinstance(data[0], list):
            # Flight data is typically in data[0][1] or similar nested structure
            # We need to find arrays that look like flight data
            def find_flight_arrays(obj, path=""):
                flights = []
                if isinstance(obj, list):
                    # Check if this looks like a flight array
                    if len(obj) > 0 and isinstance(obj[0], list):
                        # Check if first element has airline codes
                        for item in obj:
                            if isinstance(item, list) and len(item) > 0:
                                if isinstance(item[0], list) and len(item[0]) > 0:
                                    # Check for airline code pattern
                                    if isinstance(item[0][0], str) and len(item[0][0]) == 2:
                                        flights.append({
                                            'path': path,
                                            'data': item,
                                            'airline_code': item[0][0] if item[0] else None
                                        })
                
                    # Recurse
                    for idx, item in enumerate(obj):
                        flights.extend(find_flight_arrays(item, f"{path}[{idx}]"))
                
                return flights
            
            flight_arrays = find_flight_arrays(data)
            js_analysis['flight_count'] = len(flight_arrays)
            js_analysis['sample_flights'] = flight_arrays[:5]  # First 5 flights
        
    except json.JSONDecodeError as e:
        js_analysis['error'] = str(e)
    
    return js_analysis

def find_correlations(flights: List[Dict[str, Any]], js_data: Dict[str, Any]) -> Dict[str, Any]:
    """Find correlations between HTML elements and JS data."""
    correlations = {
        'url_based': {
            'reliable': False,
            'coverage': 0,
            'unique_urls': set(),
            'duplicate_urls': []
        },
        'aria_label_based': {
            'reliable': False,
            'coverage': 0,
            'patterns': []
        },
        'hierarchy_based': {
            'patterns': [],
            'container_patterns': []
        },
        'data_attributes': {
            'useful_attributes': [],
            'unique_identifiers': []
        }
    }
    
    # Analyze URL-based matching
    all_urls = []
    for flight in flights:
        for url_info in flight['urls']:
            if url_info['parsed'].get('segments'):
                all_urls.append(url_info['url'])
    
    url_counter = Counter(all_urls)
    correlations['url_based']['unique_urls'] = set(url for url, count in url_counter.items() if count == 1)
    correlations['url_based']['duplicate_urls'] = [(url, count) for url, count in url_counter.items() if count > 1]
    correlations['url_based']['coverage'] = len(all_urls) / len(flights) if flights else 0
    correlations['url_based']['reliable'] = len(correlations['url_based']['duplicate_urls']) == 0 and correlations['url_based']['coverage'] > 0.9
    
    # Analyze aria-label patterns
    aria_patterns = defaultdict(int)
    for flight in flights:
        for aria_info in flight['aria_labels']:
            parsed = aria_info['parsed']
            if parsed.get('airline') and parsed.get('price'):
                pattern = f"airline:{parsed['airline']}_price:{parsed['price']}_type:{parsed.get('flight_type', 'unknown')}"
                aria_patterns[pattern] += 1
    
    correlations['aria_label_based']['patterns'] = list(aria_patterns.items())
    correlations['aria_label_based']['coverage'] = sum(1 for f in flights if f['aria_labels']) / len(flights) if flights else 0
    
    # Analyze data attributes
    all_data_attrs = defaultdict(set)
    for flight in flights:
        for attr, values in flight['data_attributes'].items():
            for value in values:
                all_data_attrs[attr].add(value)
    
    # Find potentially useful attributes (those with many unique values)
    for attr, values in all_data_attrs.items():
        if len(values) > len(flights) * 0.5:  # Many unique values
            correlations['data_attributes']['useful_attributes'].append({
                'attribute': attr,
                'unique_values': len(values),
                'sample_values': list(values)[:5]
            })
    
    return correlations

def generate_recommendations(correlations: Dict[str, Any]) -> List[str]:
    """Generate recommendations for reliable matching strategies."""
    recommendations = []
    
    if correlations['url_based']['reliable']:
        recommendations.append(
            "PRIMARY: Use data-travelimpactmodelwebsiteurl for matching. "
            "URLs provide unique identifiers with flight numbers and routes."
        )
    else:
        recommendations.append(
            "WARNING: URL-based matching has issues: "
            f"Coverage: {correlations['url_based']['coverage']:.1%}, "
            f"Duplicate URLs: {len(correlations['url_based']['duplicate_urls'])}"
        )
    
    if correlations['aria_label_based']['coverage'] > 0.8:
        recommendations.append(
            "SECONDARY: Use aria-label parsing as fallback. "
            f"Coverage: {correlations['aria_label_based']['coverage']:.1%}"
        )
    
    if correlations['data_attributes']['useful_attributes']:
        recommendations.append(
            "ADDITIONAL: Consider these data attributes for correlation: " +
            ", ".join(attr['attribute'] for attr in correlations['data_attributes']['useful_attributes'][:3])
        )
    
    return recommendations

def main():
    # Find HTML files to analyze
    html_files = list(Path('/Users/dave/Work/flights').glob('raw_html_*.html'))
    
    if not html_files:
        print("No HTML files found!")
        return
    
    print(f"Found {len(html_files)} HTML files to analyze\n")
    
    # Analyze each file
    all_correlations = []
    
    for html_file in html_files[:5]:  # Analyze first 5 files
        print(f"\n{'='*80}")
        print(f"Analyzing: {html_file.name}")
        print('='*80)
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract flight elements
            flights = find_flight_elements(html_content)
            print(f"Found {len(flights)} flight elements")
            
            # Analyze JS data
            js_data = analyze_js_data_structure(html_content)
            print(f"JS data found: {js_data['found']}, Flight count: {js_data['flight_count']}")
            
            # Find correlations
            correlations = find_correlations(flights, js_data)
            all_correlations.append(correlations)
            
            # Print findings
            print("\nURL-based matching:")
            print(f"  - Unique URLs: {len(correlations['url_based']['unique_urls'])}")
            print(f"  - Duplicate URLs: {len(correlations['url_based']['duplicate_urls'])}")
            print(f"  - Coverage: {correlations['url_based']['coverage']:.1%}")
            print(f"  - Reliable: {correlations['url_based']['reliable']}")
            
            print("\nAria-label matching:")
            print(f"  - Coverage: {correlations['aria_label_based']['coverage']:.1%}")
            print(f"  - Unique patterns: {len(correlations['aria_label_based']['patterns'])}")
            
            print("\nUseful data attributes:")
            for attr_info in correlations['data_attributes']['useful_attributes'][:3]:
                print(f"  - {attr_info['attribute']}: {attr_info['unique_values']} unique values")
            
            # Sample flight data
            if flights:
                print("\nSample flight data:")
                flight = flights[0]
                if flight['urls']:
                    url_info = flight['urls'][0]['parsed']
                    print(f"  URL segments: {url_info.get('segments', [])}")
                if flight['aria_labels']:
                    aria_info = flight['aria_labels'][0]['parsed']
                    print(f"  Aria info: airline={aria_info.get('airline')}, price=${aria_info.get('price')}, type={aria_info.get('flight_type')}")
            
        except Exception as e:
            print(f"Error analyzing {html_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate overall recommendations
    print(f"\n{'='*80}")
    print("OVERALL RECOMMENDATIONS")
    print('='*80)
    
    # Aggregate findings
    url_reliable_count = sum(1 for c in all_correlations if c['url_based']['reliable'])
    avg_url_coverage = sum(c['url_based']['coverage'] for c in all_correlations) / len(all_correlations) if all_correlations else 0
    avg_aria_coverage = sum(c['aria_label_based']['coverage'] for c in all_correlations) / len(all_correlations) if all_correlations else 0
    
    print(f"\nReliability across {len(all_correlations)} files:")
    print(f"  - URL-based matching reliable in {url_reliable_count}/{len(all_correlations)} files")
    print(f"  - Average URL coverage: {avg_url_coverage:.1%}")
    print(f"  - Average aria-label coverage: {avg_aria_coverage:.1%}")
    
    print("\n## Recommended Matching Strategy:\n")
    print("1. **Primary Method**: Use data-travelimpactmodelwebsiteurl")
    print("   - Parse flight segments from URL (airline, flight number, airports)")
    print("   - Match with JS data using flight number + departure airport")
    print("   - Handle both direct and connecting flights")
    print()
    print("2. **Fallback Method**: Parse aria-labels")
    print("   - Extract airline, price, times from aria-label")
    print("   - Use combination of airline + price + departure time for matching")
    print()
    print("3. **Validation**: Count matching")
    print("   - Ensure flight counts match between JS and HTML")
    print("   - Use container-based grouping to handle round-trip duplicates")
    print()
    print("4. **Enhancement**: Combine multiple signals")
    print("   - Use URL as primary key")
    print("   - Validate with aria-label data")
    print("   - Fall back to index-based only when other methods fail")

if __name__ == '__main__':
    main()