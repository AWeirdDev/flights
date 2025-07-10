#!/usr/bin/env python3
"""
Test a focused subset of 20 extreme edge cases to find delay, terminal_info, alliance, on_time_performance
"""

import os
import re
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

# Check for required environment variable
if not os.environ.get("BRIGHT_DATA_API_KEY"):
    print("Error: BRIGHT_DATA_API_KEY environment variable is required")
    exit(1)

# Focused subset of extreme edge cases (20 routes)
extreme_subset = [
    # Most Delay-Prone Routes
    {
        "name": "LGA→ORD (Monday 7AM - Worst Delay Route)",
        "route": [FlightData(date="2025-08-25", from_airport="LGA", to_airport="ORD")],
        "category": "extreme_delay",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "EWR→BOS (Friday 6PM - Rush Hour)",
        "route": [FlightData(date="2025-08-22", from_airport="EWR", to_airport="BOS")],
        "category": "extreme_delay",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→LGA (Winter Storm Season)",
        "route": [FlightData(date="2025-01-15", from_airport="ORD", to_airport="LGA")],
        "category": "extreme_delay",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "BOS→DCA (Ice Storm Route)",
        "route": [FlightData(date="2025-02-10", from_airport="BOS", to_airport="DCA")],
        "category": "extreme_delay",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "MIA→JFK (Hurricane Season)",
        "route": [FlightData(date="2025-09-15", from_airport="MIA", to_airport="JFK")],
        "category": "extreme_delay",
        "target_fields": ["delay", "on_time_performance"]
    },
    
    # Peak Holiday Travel (Maximum Delays Expected)
    {
        "name": "LGA→ATL (Thanksgiving Eve)",
        "route": [FlightData(date="2025-11-26", from_airport="LGA", to_airport="ATL")],
        "category": "holiday_chaos",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→LAX (Thanksgiving Wednesday)",
        "route": [FlightData(date="2025-11-26", from_airport="ORD", to_airport="LAX")],
        "category": "holiday_chaos",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "LAX→JFK (Christmas Week)",
        "route": [FlightData(date="2025-12-23", from_airport="LAX", to_airport="JFK")],
        "category": "holiday_chaos",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ATL→LGA (Christmas Eve)",
        "route": [FlightData(date="2025-12-24", from_airport="ATL", to_airport="LGA")],
        "category": "holiday_chaos",
        "target_fields": ["delay", "on_time_performance"]
    },
    
    # Multi-Terminal International (Terminal Info Expected)
    {
        "name": "JFK→LHR (6 Terminals to 5 Terminals)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="LHR")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "alliance"]
    },
    {
        "name": "LAX→NRT (9 Terminals to International)",
        "route": [FlightData(date="2025-08-16", from_airport="LAX", to_airport="NRT")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "alliance"]
    },
    {
        "name": "JFK→CDG (International Hub to Hub)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="CDG")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "alliance"]
    },
    {
        "name": "ORD→FRA (Major Hub Connection)",
        "route": [FlightData(date="2025-08-17", from_airport="ORD", to_airport="FRA")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "alliance"]
    },
    
    # Premium Alliance Routes
    {
        "name": "SFO→FRA (Star Alliance Flagship)",
        "route": [FlightData(date="2025-08-17", from_airport="SFO", to_airport="FRA")],
        "category": "star_alliance",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "DFW→LHR (oneworld Flagship)",
        "route": [FlightData(date="2025-08-18", from_airport="DFW", to_airport="LHR")],
        "category": "oneworld",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "ATL→CDG (SkyTeam Flagship)",
        "route": [FlightData(date="2025-08-19", from_airport="ATL", to_airport="CDG")],
        "category": "skyteam",
        "target_fields": ["alliance", "terminal_info"]
    },
    
    # High-Frequency Business Routes (On-Time Stats Expected)
    {
        "name": "DCA→LGA (Business Shuttle)",
        "route": [FlightData(date="2025-08-22", from_airport="DCA", to_airport="LGA")],
        "category": "business_shuttle",
        "target_fields": ["on_time_performance", "delay"]
    },
    {
        "name": "BOS→DCA (Northeast Business)",
        "route": [FlightData(date="2025-08-22", from_airport="BOS", to_airport="DCA")],
        "category": "business_shuttle",
        "target_fields": ["on_time_performance", "delay"]
    },
    {
        "name": "LAX→SFO (California Business)",
        "route": [FlightData(date="2025-08-16", from_airport="LAX", to_airport="SFO")],
        "category": "business_shuttle",
        "target_fields": ["on_time_performance", "delay"]
    },
    
    # Red-Eye Flights (Different Data Sets)
    {
        "name": "LAX→JFK (Red-Eye Overnight)",
        "route": [FlightData(date="2025-08-20", from_airport="LAX", to_airport="JFK")],
        "category": "redeye",
        "target_fields": ["delay", "on_time_performance"]
    }
]

def enhanced_keyword_search(html_content, route_name):
    """Enhanced keyword search with comprehensive patterns"""
    keywords = {
        'delay': [
            'delay', 'delayed', 'late', 'behind schedule', 'running late',
            'departure delay', 'arrival delay', 'min delay', 'hour delay', 'hrs delay',
            'delayed by', 'running behind', 'expected delay', 'delay expected',
            'weather delay', 'mechanical delay', 'air traffic delay', 'delayed departure',
            'delayed arrival', 'delay due to', 'delay info', 'delay status'
        ],
        'terminal': [
            'terminal', 'gate', 'concourse', 'pier', 'departure gate', 'arrival gate',
            'terminal 1', 'terminal 2', 'terminal 3', 'terminal 4', 'terminal 5',
            'terminal a', 'terminal b', 'terminal c', 'terminal d', 'terminal e',
            'gate a', 'gate b', 'gate c', 'concourse a', 'concourse b', 'concourse c',
            'departure terminal', 'arrival terminal', 'terminal change', 'gate change',
            'departs from terminal', 'arrives at terminal', 'terminal info'
        ],
        'alliance': [
            'alliance', 'star alliance', 'oneworld', 'skyteam', 'sky team',
            'member of', 'alliance member', 'alliance partner', 'alliance network',
            'star alliance member', 'oneworld member', 'skyteam member',
            'alliance benefits', 'alliance status'
        ],
        'on_time': [
            'on-time', 'on time', 'ontime', 'punctuality', 'reliability',
            '% on time', 'percent on time', 'on-time performance', 'on-time rate',
            'punctual', 'reliable', 'delay statistics', 'performance score',
            'on time arrival', 'on time departure', 'punctuality rate'
        ]
    }
    
    findings = {}
    
    for category, terms in keywords.items():
        findings[category] = []
        for term in terms:
            # Case insensitive search with word boundaries where possible
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(html_content)
            
            for match in matches:
                # Get extended context around the match
                start = max(0, match.start() - 200)
                end = min(len(html_content), match.end() + 200)
                context = html_content[start:end]
                
                # Clean up the context
                context = ' '.join(context.split())
                
                findings[category].append({
                    'term': term,
                    'position': match.start(),
                    'context': context
                })
    
    return findings

def extract_flight_specific_aria_labels(html_content):
    """Extract aria-labels specifically from flight items and analyze for keywords"""
    from selectolax.lexbor import LexborHTMLParser
    
    parser = LexborHTMLParser(html_content)
    
    # Get flight containers like the actual parser does
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    
    flight_aria_labels = []
    keyword_matches = []
    
    for i, container in enumerate(flight_containers):
        # Get flight items within this container
        flight_items = container.css("ul.Rk10dc li")
        
        for j, item in enumerate(flight_items):
            # Get all aria-labels within this flight item
            aria_elements = item.css('*[aria-label]')
            
            for elem in aria_elements:
                aria_label = elem.attributes.get('aria-label', '')
                if aria_label:
                    flight_aria_labels.append({
                        'container': i,
                        'item': j,
                        'tag': elem.tag,
                        'classes': elem.attributes.get('class', ''),
                        'aria_label': aria_label
                    })
                    
                    # Check for keywords in this specific flight's aria-label
                    keywords_found = []
                    aria_lower = aria_label.lower()
                    
                    # More comprehensive keyword detection
                    delay_keywords = ['delay', 'late', 'behind', 'delayed', 'running late']
                    terminal_keywords = ['terminal', 'gate', 'concourse', 'pier', 'departure gate', 'arrival gate']
                    alliance_keywords = ['alliance', 'oneworld', 'skyteam', 'star alliance', 'member']
                    ontime_keywords = ['on-time', 'on time', 'punctual', '% on time', 'reliability', 'performance']
                    
                    if any(word in aria_lower for word in delay_keywords):
                        keywords_found.append('delay')
                    if any(word in aria_lower for word in terminal_keywords):
                        keywords_found.append('terminal')
                    if any(word in aria_lower for word in alliance_keywords):
                        keywords_found.append('alliance')
                    if any(word in aria_lower for word in ontime_keywords):
                        keywords_found.append('on_time')
                    
                    if keywords_found:
                        keyword_matches.append({
                            'container': i,
                            'item': j,
                            'tag': elem.tag,
                            'classes': elem.attributes.get('class', ''),
                            'keywords': keywords_found,
                            'aria_label': aria_label
                        })
    
    return flight_aria_labels, keyword_matches

def analyze_fields_detailed(flights, route_name):
    """Detailed field analysis"""
    total_flights = len(flights)
    
    field_counts = {
        'delay': 0,
        'operated_by': 0,
        'terminal_info': 0,
        'alliance': 0,
        'on_time_performance': 0
    }
    
    field_samples = {
        'delay': [],
        'operated_by': [],
        'terminal_info': [],
        'alliance': [],
        'on_time_performance': []
    }
    
    for flight in flights:
        # Count non-null fields and collect samples
        if flight.delay is not None:
            field_counts['delay'] += 1
            if len(field_samples['delay']) < 3:
                field_samples['delay'].append(flight.delay)
        
        if flight.operated_by is not None:
            field_counts['operated_by'] += 1
            if len(field_samples['operated_by']) < 3:
                field_samples['operated_by'].append(flight.operated_by)
        
        if flight.terminal_info is not None:
            field_counts['terminal_info'] += 1
            if len(field_samples['terminal_info']) < 3:
                field_samples['terminal_info'].append(flight.terminal_info)
        
        if flight.alliance is not None:
            field_counts['alliance'] += 1
            if len(field_samples['alliance']) < 3:
                field_samples['alliance'].append(flight.alliance)
        
        if flight.on_time_performance is not None:
            field_counts['on_time_performance'] += 1
            if len(field_samples['on_time_performance']) < 3:
                field_samples['on_time_performance'].append(flight.on_time_performance)
    
    return field_counts, field_samples, total_flights

def test_route_extreme(route_info):
    """Test extreme edge case route with comprehensive analysis"""
    try:
        # Create filter
        filter = create_filter(
            flight_data=route_info['route'],
            trip="one-way",
            passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
            seat="economy",
            max_stops=None,
        )
        
        # Get flights using Bright Data with hybrid data source
        result = get_flights_from_filter(filter, mode="bright-data")
        
        if not result or not result.flights:
            return {
                'name': route_info['name'],
                'category': route_info['category'],
                'target_fields': route_info['target_fields'],
                'success': False,
                'error': 'No flights found',
                'analysis': None
            }
        
        # Get raw HTML for deep analysis
        from fast_flights.bright_data_fetch import bright_data_fetch
        data = filter.as_b64()
        params = {
            "tfs": data.decode("utf-8"),
            "hl": "en", 
            "tfu": "EgQIABABIgA",
            "curr": "",
        }
        raw_response = bright_data_fetch(params)
        
        # Comprehensive analysis
        keyword_findings = enhanced_keyword_search(raw_response.text, route_info['name'])
        flight_aria_labels, aria_keyword_matches = extract_flight_specific_aria_labels(raw_response.text)
        field_counts, field_samples, total_flights = analyze_fields_detailed(result.flights, route_info['name'])
        
        # Save raw HTML if any keywords found
        keyword_count = sum(len(findings) for findings in keyword_findings.values())
        if keyword_count > 0 or aria_keyword_matches:
            filename = f"extreme_html_{route_info['name'].replace('→', '_').replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')}.html"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(raw_response.text)
            except:
                pass  # Continue if file save fails
        
        return {
            'name': route_info['name'],
            'category': route_info['category'],
            'target_fields': route_info['target_fields'],
            'success': True,
            'error': None,
            'analysis': {
                'field_counts': field_counts,
                'field_samples': field_samples,
                'total_flights': total_flights,
                'current_price': result.current_price,
                'keyword_findings': keyword_findings,
                'aria_keyword_matches': aria_keyword_matches,
                'total_flight_aria_labels': len(flight_aria_labels),
                'keyword_count': keyword_count
            }
        }
        
    except Exception as e:
        return {
            'name': route_info['name'],
            'category': route_info['category'],
            'target_fields': route_info['target_fields'],
            'success': False,
            'error': f"{type(e).__name__}: {e}",
            'analysis': None
        }

def main():
    """Main testing function"""
    print("EXTREME EDGE CASE SUBSET TESTING")
    print("=" * 70)
    print(f"Testing {len(extreme_subset)} most extreme routes for missing fields")
    print("Focus: delay, terminal_info, alliance, on_time_performance")
    
    # Execute subset in parallel
    print(f"\nExecuting {len(extreme_subset)} extreme routes in parallel...")
    results = []
    
    with ThreadPoolExecutor(max_workers=len(extreme_subset)) as executor:
        # Submit all tasks
        future_to_route = {executor.submit(test_route_extreme, route_info): route_info for route_info in extreme_subset}
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_route):
            route_info = future_to_route[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1
                status = "✅" if result['success'] else "❌"
                print(f"{status} [{completed}/{len(extreme_subset)}] {result['name']}")
            except Exception as exc:
                completed += 1
                print(f"❌ [{completed}/{len(extreme_subset)}] {route_info['name']} - {exc}")
    
    # Analyze results
    print(f"\n{'='*70}")
    print("EXTREME EDGE CASE ANALYSIS")
    print(f"{'='*70}")
    
    # Track discoveries
    field_discoveries = {
        'delay': [],
        'terminal_info': [],
        'alliance': [],
        'on_time_performance': []
    }
    
    keyword_discoveries = {
        'delay': [],
        'terminal': [],
        'alliance': [],
        'on_time': []
    }
    
    aria_discoveries = []
    successful_tests = 0
    total_flights = 0
    total_keywords = 0
    
    # Process results
    for result in results:
        if result['success'] and result['analysis']:
            successful_tests += 1
            analysis = result['analysis']
            total_flights += analysis['total_flights']
            total_keywords += analysis['keyword_count']
            
            # Check field discoveries
            for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance']:
                if analysis['field_counts'][field] > 0:
                    field_discoveries[field].append({
                        'route': result['name'],
                        'category': result['category'],
                        'count': analysis['field_counts'][field],
                        'total': analysis['total_flights'],
                        'samples': analysis['field_samples'][field]
                    })
            
            # Check keyword discoveries
            for category, findings in analysis['keyword_findings'].items():
                if findings:
                    keyword_discoveries[category].append({
                        'route': result['name'],
                        'category': result['category'],
                        'count': len(findings),
                        'terms': list(set([f['term'] for f in findings]))
                    })
            
            # Check aria-label discoveries
            if analysis['aria_keyword_matches']:
                aria_discoveries.append({
                    'route': result['name'],
                    'category': result['category'],
                    'matches': analysis['aria_keyword_matches']
                })
    
    # Report findings
    print(f"\n🎯 FIELD DISCOVERIES:")
    field_found = False
    for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance']:
        if field_discoveries[field]:
            field_found = True
            print(f"\n🎉 {field.upper()} FOUND!")
            for disc in field_discoveries[field]:
                percentage = (disc['count'] / disc['total']) * 100
                print(f"  ✅ {disc['route']}: {disc['count']}/{disc['total']} ({percentage:.1f}%)")
                if disc['samples']:
                    print(f"     Examples: {disc['samples']}")
        else:
            print(f"\n❌ {field.upper()}: Not found")
    
    print(f"\n🔍 KEYWORD DISCOVERIES:")
    keyword_found = False
    for category in ['delay', 'terminal', 'alliance', 'on_time']:
        if keyword_discoveries[category]:
            keyword_found = True
            print(f"\n⚠️  {category.upper()} KEYWORDS FOUND!")
            for disc in keyword_discoveries[category]:
                print(f"  🔍 {disc['route']}: {disc['count']} matches")
                print(f"     Terms: {disc['terms'][:5]}")  # Show first 5 terms
        else:
            print(f"\n❌ {category.upper()}: No keywords")
    
    print(f"\n🏷️  ARIA-LABEL DISCOVERIES:")
    if aria_discoveries:
        print(f"\n⚠️  ARIA-LABEL KEYWORDS FOUND!")
        for disc in aria_discoveries:
            print(f"  🏷️  {disc['route']}:")
            for match in disc['matches'][:2]:  # Show first 2
                print(f"     Keywords: {match['keywords']}")
                print(f"     Label: {match['aria_label'][:100]}...")
    else:
        print(f"\n❌ No keyword matches in aria-labels")
    
    # Summary
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"Extreme routes tested: {successful_tests}/{len(extreme_subset)}")
    print(f"Total flights analyzed: {total_flights}")
    print(f"Total keyword matches: {total_keywords}")
    
    if field_found:
        print(f"\n🎉 SUCCESS: Found target fields in parsed data!")
    elif keyword_found or aria_discoveries:
        print(f"\n⚠️  PARTIAL: Keywords found in HTML but not extracted")
        print(f"Extraction logic may need refinement")
    else:
        print(f"\n❌ NO DISCOVERIES: Fields not found in extreme edge cases")
        print(f"Strong evidence fields are not available in API responses")

if __name__ == "__main__":
    main()