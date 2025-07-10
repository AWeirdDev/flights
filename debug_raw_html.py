#!/usr/bin/env python3
"""
Debug script to analyze raw HTML responses for missing fields
This script will fetch raw HTML, save it to files, and search for keywords
"""

import os
import re
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from fast_flights import create_filter, FlightData, Passengers
from fast_flights.bright_data_fetch import bright_data_fetch
from fast_flights.filter import TFSData
from selectolax.lexbor import LexborHTMLParser

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

# Representative routes for debugging
debug_routes = [
    {
        "name": "JFK-LAX-domestic",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="LAX")],
        "expected_info": "Basic domestic route, should have operated_by"
    },
    {
        "name": "LHR-CDG-european",
        "route": [FlightData(date="2025-08-15", from_airport="LHR", to_airport="CDG")],
        "expected_info": "European route, may have alliance info"
    },
    {
        "name": "SFO-FRA-international",
        "route": [FlightData(date="2025-08-15", from_airport="SFO", to_airport="FRA")],
        "expected_info": "International route, may have terminal/alliance"
    },
    {
        "name": "ORD-LGA-delay-prone",
        "route": [FlightData(date="2025-08-15", from_airport="ORD", to_airport="LGA")],
        "expected_info": "Delay-prone route, may have delay info"
    },
    {
        "name": "DFW-LHR-oneworld",
        "route": [FlightData(date="2025-08-15", from_airport="DFW", to_airport="LHR")],
        "expected_info": "American Airlines route, may have oneworld alliance"
    },
    {
        "name": "JFK-NRT-long-haul",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="NRT")],
        "expected_info": "Long-haul route, may have terminal/alliance"
    }
]

def fetch_raw_html(route_info):
    """Fetch raw HTML for a route"""
    try:
        # Create filter
        filter = create_filter(
            flight_data=route_info['route'],
            trip="one-way",
            passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
            seat="economy",
            max_stops=None,
        )
        
        # Get raw HTML response
        data = filter.as_b64()
        params = {
            "tfs": data.decode("utf-8"),
            "hl": "en",
            "tfu": "EgQIABABIgA",
            "curr": "",
        }
        
        response = bright_data_fetch(params)
        
        # Save raw HTML to file
        filename = f"raw_html_{route_info['name']}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return {
            'name': route_info['name'],
            'expected_info': route_info['expected_info'],
            'success': True,
            'html': response.text,
            'filename': filename,
            'length': len(response.text)
        }
        
    except Exception as e:
        return {
            'name': route_info['name'],
            'expected_info': route_info['expected_info'],
            'success': False,
            'error': str(e),
            'html': None,
            'filename': None,
            'length': 0
        }

def search_keywords_in_html(html_content, route_name):
    """Search for keywords related to missing fields in HTML"""
    keywords = {
        'delay': ['delay', 'delayed', 'late', 'departure delay', 'arrival delay', 'min delay', 'hour delay'],
        'terminal': ['terminal', 'gate', 'terminal 1', 'terminal 2', 'terminal 3', 'terminal 4', 'terminal 5'],
        'alliance': ['alliance', 'star alliance', 'oneworld', 'skyteam', 'sky team'],
        'on_time': ['on-time', 'on time', 'ontime', '% on time', 'punctuality', 'reliability']
    }
    
    findings = {}
    
    for category, terms in keywords.items():
        findings[category] = []
        for term in terms:
            # Case insensitive search
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            matches = pattern.finditer(html_content)
            
            for match in matches:
                # Get context around the match
                start = max(0, match.start() - 100)
                end = min(len(html_content), match.end() + 100)
                context = html_content[start:end]
                
                # Clean up the context
                context = ' '.join(context.split())
                
                findings[category].append({
                    'term': term,
                    'position': match.start(),
                    'context': context
                })
    
    return findings

def extract_all_aria_labels(html_content):
    """Extract all aria-labels from the HTML"""
    parser = LexborHTMLParser(html_content)
    
    # Get all elements with aria-label
    aria_elements = parser.css('*[aria-label]')
    
    aria_labels = []
    for elem in aria_elements:
        aria_label = elem.attributes.get('aria-label', '')
        if aria_label:
            aria_labels.append({
                'tag': elem.tag,
                'classes': elem.attributes.get('class', ''),
                'aria_label': aria_label
            })
    
    return aria_labels

def analyze_flight_containers(html_content):
    """Analyze the flight container structure"""
    parser = LexborHTMLParser(html_content)
    
    # Find flight containers
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    
    analysis = {
        'container_count': len(flight_containers),
        'flight_items': [],
        'total_items': 0
    }
    
    for i, container in enumerate(flight_containers):
        items = container.css("ul.Rk10dc li")
        analysis['total_items'] += len(items)
        
        # Analyze first few items in detail
        for j, item in enumerate(items[:3]):
            item_analysis = {
                'container_index': i,
                'item_index': j,
                'classes': item.attributes.get('class', ''),
                'aria_label': item.attributes.get('aria-label', ''),
                'child_aria_labels': []
            }
            
            # Get child elements with aria-labels
            child_elements = item.css('*[aria-label]')
            for child in child_elements:
                item_analysis['child_aria_labels'].append({
                    'tag': child.tag,
                    'classes': child.attributes.get('class', ''),
                    'aria_label': child.attributes.get('aria-label', '')[:200] + '...' if len(child.attributes.get('aria-label', '')) > 200 else child.attributes.get('aria-label', '')
                })
            
            analysis['flight_items'].append(item_analysis)
    
    return analysis

def main():
    """Main debugging function"""
    print("Raw HTML Debugging Analysis")
    print("=" * 70)
    print("Fetching raw HTML responses to debug missing fields")
    print("This will save HTML files and search for keywords")
    
    # Fetch raw HTML for all routes
    print(f"\nFetching raw HTML for {len(debug_routes)} routes...")
    results = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_route = {executor.submit(fetch_raw_html, route_info): route_info for route_info in debug_routes}
        
        for future in as_completed(future_to_route):
            route_info = future_to_route[future]
            try:
                result = future.result()
                results.append(result)
                status = "✅" if result['success'] else "❌"
                print(f"{status} {result['name']}: {result.get('length', 0)} chars")
            except Exception as exc:
                print(f"❌ {route_info['name']}: {exc}")
    
    # Analyze each successful result
    print(f"\n{'='*70}")
    print("DETAILED ANALYSIS")
    print(f"{'='*70}")
    
    for result in results:
        if not result['success']:
            print(f"\n❌ {result['name']}: {result['error']}")
            continue
        
        print(f"\n🔍 ANALYZING: {result['name']}")
        print(f"Expected: {result['expected_info']}")
        print(f"HTML saved to: {result['filename']}")
        print(f"Size: {result['length']} characters")
        
        # Search for keywords
        print(f"\n📝 KEYWORD SEARCH:")
        keyword_findings = search_keywords_in_html(result['html'], result['name'])
        
        for category, findings in keyword_findings.items():
            if findings:
                print(f"  ✅ {category.upper()}: {len(findings)} matches")
                for finding in findings[:3]:  # Show first 3 matches
                    print(f"    • '{finding['term']}' at position {finding['position']}")
                    print(f"      Context: {finding['context']}")
            else:
                print(f"  ❌ {category.upper()}: No matches")
        
        # Analyze aria-labels
        print(f"\n🏷️  ARIA-LABEL ANALYSIS:")
        aria_labels = extract_all_aria_labels(result['html'])
        print(f"  Total elements with aria-label: {len(aria_labels)}")
        
        # Look for interesting aria-labels
        flight_aria_labels = [al for al in aria_labels if 'flight' in al['aria_label'].lower() or 'JMc5Xc' in al['classes']]
        print(f"  Flight-related aria-labels: {len(flight_aria_labels)}")
        
        for aria in flight_aria_labels[:3]:  # Show first 3
            print(f"    • <{aria['tag']}> class='{aria['classes']}'")
            print(f"      {aria['aria_label'][:150]}...")
        
        # Analyze flight container structure
        print(f"\n🏗️  FLIGHT CONTAINER ANALYSIS:")
        container_analysis = analyze_flight_containers(result['html'])
        print(f"  Flight containers found: {container_analysis['container_count']}")
        print(f"  Total flight items: {container_analysis['total_items']}")
        
        # Show detailed analysis of first few items
        if container_analysis['flight_items']:
            print(f"  First few items:")
            for item in container_analysis['flight_items'][:2]:
                print(f"    Item {item['item_index']} in container {item['container_index']}:")
                print(f"      Classes: {item['classes']}")
                print(f"      Item aria-label: {item['aria_label'][:100]}...")
                print(f"      Child aria-labels: {len(item['child_aria_labels'])}")
    
    # Final summary
    print(f"\n{'='*70}")
    print("DEBUGGING SUMMARY")
    print(f"{'='*70}")
    
    successful_routes = [r for r in results if r['success']]
    print(f"Successfully analyzed: {len(successful_routes)}/{len(debug_routes)} routes")
    
    # Check if we found any evidence of missing fields
    total_delay_matches = 0
    total_terminal_matches = 0
    total_alliance_matches = 0
    total_ontime_matches = 0
    
    for result in successful_routes:
        keyword_findings = search_keywords_in_html(result['html'], result['name'])
        total_delay_matches += len(keyword_findings['delay'])
        total_terminal_matches += len(keyword_findings['terminal'])
        total_alliance_matches += len(keyword_findings['alliance'])
        total_ontime_matches += len(keyword_findings['on_time'])
    
    print(f"\nKeyword matches found:")
    print(f"  Delay-related: {total_delay_matches}")
    print(f"  Terminal-related: {total_terminal_matches}")
    print(f"  Alliance-related: {total_alliance_matches}")
    print(f"  On-time-related: {total_ontime_matches}")
    
    if any([total_delay_matches, total_terminal_matches, total_alliance_matches, total_ontime_matches]):
        print(f"\n🎯 BREAKTHROUGH: Found keywords in raw HTML!")
        print(f"This suggests the information IS present but extraction patterns need fixing.")
    else:
        print(f"\n❌ NO KEYWORDS FOUND: The fields may truly not be present in the responses.")
    
    print(f"\n📁 Raw HTML files saved for manual inspection:")
    for result in successful_routes:
        print(f"  - {result['filename']}")
    
    print(f"\n💡 Next steps:")
    print(f"  1. Manually inspect the saved HTML files")
    print(f"  2. Look for patterns in aria-labels that might contain this information")
    print(f"  3. Update extraction logic based on findings")

if __name__ == "__main__":
    main()