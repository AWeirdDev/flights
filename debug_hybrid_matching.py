#!/usr/bin/env python3
"""Debug script to analyze why hybrid mode loses 5 arrival_time_ahead values."""

import sys
import json
import re
from typing import List, Dict, Any, Tuple
from selectolax.lexbor import LexborHTMLParser

# Add the project to path
sys.path.insert(0, '/Users/dave/Work/flights')

from fast_flights.core import (
    extract_html_enrichments, 
    convert_decoded_to_result,
    combine_results,
    parse_response,
    DataSource
)
from fast_flights.decoder import ResultDecoder
from fast_flights.flights_impl import FlightData, Passengers
from fast_flights.filter import TFSData
from fast_flights.core import get_flights_from_filter


def analyze_enrichments(enrichments: List[dict]) -> Dict[str, Any]:
    """Analyze HTML enrichments to understand what we have."""
    stats = {
        'total': len(enrichments),
        'with_arrival_time_ahead': 0,
        'with_url': 0,
        'with_emissions': 0,
        'with_operated_by': 0,
        'arrival_time_ahead_values': [],
        'urls': []
    }
    
    for idx, enrichment in enumerate(enrichments):
        if 'arrival_time_ahead' in enrichment and enrichment['arrival_time_ahead']:
            stats['with_arrival_time_ahead'] += 1
            stats['arrival_time_ahead_values'].append({
                'index': idx,
                'value': enrichment['arrival_time_ahead'],
                'url': enrichment.get('url', 'NO_URL')
            })
        
        if 'url' in enrichment and enrichment['url']:
            stats['with_url'] += 1
            stats['urls'].append(enrichment['url'])
        
        if 'emissions' in enrichment:
            stats['with_emissions'] += 1
        
        if 'operated_by' in enrichment:
            stats['with_operated_by'] += 1
    
    return stats


def analyze_js_flights(js_result) -> Dict[str, Any]:
    """Analyze JS flights to understand what we're matching against."""
    stats = {
        'total': len(js_result.flights),
        'with_flight_number': 0,
        'with_airports': 0,
        'flight_details': []
    }
    
    for idx, flight in enumerate(js_result.flights):
        has_flight_number = bool(flight.flight_number)
        has_airports = bool(flight.departure_airport and flight.arrival_airport)
        
        if has_flight_number:
            stats['with_flight_number'] += 1
        if has_airports:
            stats['with_airports'] += 1
        
        # Build expected URL pattern
        expected_url_pattern = None
        if flight.flight_number and flight.departure_airport and flight.arrival_airport:
            flight_num_for_url = flight.flight_number.replace(' ', '-')
            expected_url_pattern = f"{flight.departure_airport}-{flight.arrival_airport}-{flight_num_for_url}"
        
        stats['flight_details'].append({
            'index': idx,
            'flight_number': flight.flight_number,
            'departure': flight.departure_airport,
            'arrival': flight.arrival_airport,
            'expected_url_pattern': expected_url_pattern,
            'has_arrival_time_ahead': bool(flight.arrival_time_ahead),
            'arrival_time_ahead_value': flight.arrival_time_ahead if flight.arrival_time_ahead else None
        })
    
    return stats


def find_matching_issues(enrichments: List[dict], js_result) -> List[Dict[str, Any]]:
    """Find which enrichments with arrival_time_ahead fail to match."""
    issues = []
    
    # Create enrichment mapping by URL
    enrichment_by_url = {}
    for enrichment in enrichments:
        if 'url' in enrichment and enrichment['url']:
            enrichment_by_url[enrichment['url']] = enrichment
    
    # Also keep enrichments by index
    enrichments_by_index = {i: e for i, e in enumerate(enrichments)}
    
    # Track which enrichments get matched
    matched_enrichment_indices = set()
    
    # Simulate the matching logic from combine_results
    for i, flight in enumerate(js_result.flights):
        enrichment = None
        matched_by = None
        
        # First, try URL matching
        if flight.flight_number and flight.departure_airport and flight.arrival_airport:
            flight_num_for_url = flight.flight_number.replace(' ', '-')
            
            for url, enrich in enrichment_by_url.items():
                if flight_num_for_url in url:
                    if f"{flight.departure_airport}-{flight.arrival_airport}-{flight_num_for_url}" in url:
                        enrichment = enrich
                        matched_by = 'url_direct'
                        break
                    elif f"{flight.departure_airport}-" in url and flight_num_for_url in url.split(',')[0]:
                        enrichment = enrich
                        matched_by = 'url_connecting'
                        break
        
        # Fall back to index matching
        if enrichment is None and i in enrichments_by_index:
            enrichment = enrichments_by_index[i]
            matched_by = 'index'
        
        # Track which enrichment index was matched
        if enrichment:
            for idx, e in enumerate(enrichments):
                if e is enrichment:
                    matched_enrichment_indices.add(idx)
                    break
    
    # Now find enrichments with arrival_time_ahead that weren't matched
    for idx, enrichment in enumerate(enrichments):
        if 'arrival_time_ahead' in enrichment and enrichment['arrival_time_ahead']:
            if idx not in matched_enrichment_indices:
                # This enrichment has arrival_time_ahead but wasn't matched
                issues.append({
                    'enrichment_index': idx,
                    'arrival_time_ahead': enrichment['arrival_time_ahead'],
                    'url': enrichment.get('url', 'NO_URL'),
                    'reason': 'Not matched to any JS flight'
                })
    
    return issues


def main():
    """Run the debugging analysis."""
    print("=== Debugging Hybrid Mode Arrival Time Ahead Loss ===\n")
    
    # Define test flight parameters
    flight_data = [
        FlightData(
            date="2025-08-16",
            from_airport="LAX",
            to_airport="JFK"
        )
    ]
    
    passengers = Passengers(adults=1)
    
    print("1. Fetching flights in HTML mode...")
    html_result = get_flights_from_filter(
        TFSData.from_interface(
            flight_data=flight_data,
            trip="one-way",
            passengers=passengers,
            seat="economy",
            max_stops=None
        ),
        mode="bright-data",
        data_source="html"
    )
    
    html_arrival_time_ahead_count = sum(1 for f in html_result.flights if f.arrival_time_ahead)
    print(f"   HTML mode: {html_arrival_time_ahead_count} flights with arrival_time_ahead")
    
    print("\n2. Fetching flights in hybrid mode...")
    # We need to fetch the raw response to analyze it
    from fast_flights.bright_data_fetch import bright_data_fetch
    
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
    
    # Extract JS data
    script = parser.css_first(r'script.ds\:1').text()
    match = re.search(r'^.*?\{.*?data:(\[.*\]).*\}', script)
    data = json.loads(match.group(1))
    decoded = ResultDecoder.decode(data)
    js_result = convert_decoded_to_result(decoded)
    
    # Extract HTML enrichments
    html_enrichments = extract_html_enrichments(parser, res.text)
    
    print(f"\n3. Analyzing enrichments...")
    enrichment_stats = analyze_enrichments(html_enrichments)
    print(f"   Total enrichments: {enrichment_stats['total']}")
    print(f"   With arrival_time_ahead: {enrichment_stats['with_arrival_time_ahead']}")
    print(f"   With URL: {enrichment_stats['with_url']}")
    
    print(f"\n4. Analyzing JS flights...")
    js_stats = analyze_js_flights(js_result)
    print(f"   Total JS flights: {js_stats['total']}")
    print(f"   With flight_number: {js_stats['with_flight_number']}")
    print(f"   With airports: {js_stats['with_airports']}")
    
    print(f"\n5. Finding matching issues...")
    issues = find_matching_issues(html_enrichments, js_result)
    
    if issues:
        print(f"   Found {len(issues)} enrichments with arrival_time_ahead that fail to match:")
        for issue in issues:
            print(f"\n   Issue #{issue['enrichment_index']}:")
            print(f"     - arrival_time_ahead: {issue['arrival_time_ahead']}")
            print(f"     - URL: {issue['url']}")
            print(f"     - Reason: {issue['reason']}")
    
    # Now apply combine_results and check
    print(f"\n6. Applying combine_results...")
    hybrid_result = combine_results(js_result, html_enrichments)
    hybrid_arrival_time_ahead_count = sum(1 for f in hybrid_result.flights if f.arrival_time_ahead)
    print(f"   Hybrid mode: {hybrid_arrival_time_ahead_count} flights with arrival_time_ahead")
    
    print(f"\n7. Detailed matching analysis...")
    print(f"   Enrichments with arrival_time_ahead:")
    for item in enrichment_stats['arrival_time_ahead_values']:
        print(f"     Index {item['index']}: {item['value']} - URL: {item['url']}")
    
    print(f"\n   JS flights expecting to match:")
    for i in range(min(10, len(js_stats['flight_details']))):  # Show first 10
        detail = js_stats['flight_details'][i]
        print(f"     Index {detail['index']}: {detail['flight_number']} ({detail['departure']}-{detail['arrival']})")
        print(f"       Expected URL pattern: {detail['expected_url_pattern']}")
    
    # Find specific mismatches
    print(f"\n8. Finding specific mismatches...")
    
    # Check if it's an index mismatch issue
    if len(html_enrichments) != len(js_result.flights):
        print(f"   WARNING: Count mismatch!")
        print(f"   - HTML enrichments: {len(html_enrichments)}")
        print(f"   - JS flights: {len(js_result.flights)}")
        
    # Look for pattern differences
    print(f"\n9. Analyzing URL patterns...")
    print("   Sample enrichment URLs:")
    for i, url in enumerate(enrichment_stats['urls'][:5]):
        print(f"     {i}: {url}")
    
    print("\n   Sample JS flight patterns:")
    for i in range(min(5, len(js_stats['flight_details']))):
        detail = js_stats['flight_details'][i]
        if detail['expected_url_pattern']:
            print(f"     {i}: {detail['expected_url_pattern']}")


if __name__ == "__main__":
    main()