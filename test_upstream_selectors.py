#!/usr/bin/env python3
"""
Test if the upstream/main branch CSS selectors work with the downloaded HTML files
"""

import os
import glob
from selectolax.lexbor import LexborHTMLParser

def test_css_selectors(html_file):
    """Test if the CSS selectors from upstream/main work"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    parser = LexborHTMLParser(html_content)
    
    results = {
        'file': html_file,
        'delay_selector': {
            'selector': '.GsCCve',
            'matches': 0,
            'samples': []
        },
        'time_ahead_selector': {
            'selector': 'span.bOzv6',
            'matches': 0,
            'samples': []
        },
        'flight_containers': {
            'selector': 'div[jsname="IWWDBc"], div[jsname="YdtKid"]',
            'matches': 0
        },
        'flight_items': {
            'selector': 'ul.Rk10dc li',
            'total': 0
        }
    }
    
    # Test delay selector (.GsCCve)
    delay_elements = parser.css('.GsCCve')
    results['delay_selector']['matches'] = len(delay_elements)
    for elem in delay_elements[:3]:  # First 3 samples
        results['delay_selector']['samples'].append({
            'text': elem.text(strip=True),
            'parent_classes': elem.parent.attributes.get('class', '') if elem.parent else '',
            'html': str(elem.html)[:100]
        })
    
    # Test time ahead selector (span.bOzv6)
    time_ahead_elements = parser.css('span.bOzv6')
    results['time_ahead_selector']['matches'] = len(time_ahead_elements)
    for elem in time_ahead_elements[:3]:  # First 3 samples
        results['time_ahead_selector']['samples'].append({
            'text': elem.text(strip=True),
            'parent_classes': elem.parent.attributes.get('class', '') if elem.parent else '',
            'html': str(elem.html)[:100]
        })
    
    # Test flight containers
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    results['flight_containers']['matches'] = len(flight_containers)
    
    # Test flight items
    total_items = 0
    for container in flight_containers:
        items = container.css('ul.Rk10dc li')
        total_items += len(items)
    results['flight_items']['total'] = total_items
    
    return results

def main():
    """Test all downloaded HTML files"""
    print("TESTING UPSTREAM/MAIN CSS SELECTORS")
    print("=" * 70)
    
    # Find all HTML files from the extreme edge case test
    html_files = glob.glob('extreme_html_*.html')
    if not html_files:
        # Try other HTML files
        html_files = glob.glob('raw_html_*.html')
    
    if not html_files:
        print("No HTML files found. Please run debug_raw_html.py or test_extreme_edge_cases.py first.")
        return
    
    print(f"Found {len(html_files)} HTML files to test\n")
    
    # Track overall statistics
    total_delay_matches = 0
    total_time_ahead_matches = 0
    total_flight_containers = 0
    total_flight_items = 0
    files_with_delay = 0
    files_with_time_ahead = 0
    
    # Test each file
    for html_file in html_files[:10]:  # Test first 10 files
        print(f"\nTesting: {html_file}")
        print("-" * 50)
        
        results = test_css_selectors(html_file)
        
        # Update totals
        total_delay_matches += results['delay_selector']['matches']
        total_time_ahead_matches += results['time_ahead_selector']['matches']
        total_flight_containers += results['flight_containers']['matches']
        total_flight_items += results['flight_items']['total']
        
        if results['delay_selector']['matches'] > 0:
            files_with_delay += 1
        if results['time_ahead_selector']['matches'] > 0:
            files_with_time_ahead += 1
        
        # Print results
        print(f"  Flight containers: {results['flight_containers']['matches']}")
        print(f"  Flight items: {results['flight_items']['total']}")
        print(f"  Delay selector (.GsCCve): {results['delay_selector']['matches']} matches")
        if results['delay_selector']['samples']:
            print("    Samples:")
            for sample in results['delay_selector']['samples']:
                print(f"      Text: '{sample['text']}'")
                print(f"      Parent classes: '{sample['parent_classes']}'")
        
        print(f"  Time ahead selector (span.bOzv6): {results['time_ahead_selector']['matches']} matches")
        if results['time_ahead_selector']['samples']:
            print("    Samples:")
            for sample in results['time_ahead_selector']['samples']:
                print(f"      Text: '{sample['text']}'")
                print(f"      Parent classes: '{sample['parent_classes']}'")
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Files tested: {min(len(html_files), 10)}")
    print(f"Total flight containers: {total_flight_containers}")
    print(f"Total flight items: {total_flight_items}")
    print(f"\nDELAY SELECTOR (.GsCCve):")
    print(f"  Files with matches: {files_with_delay}/{min(len(html_files), 10)}")
    print(f"  Total matches: {total_delay_matches}")
    print(f"\nTIME AHEAD SELECTOR (span.bOzv6):")
    print(f"  Files with matches: {files_with_time_ahead}/{min(len(html_files), 10)}")
    print(f"  Total matches: {total_time_ahead_matches}")
    
    if total_delay_matches == 0 and total_time_ahead_matches == 0:
        print(f"\n⚠️  WARNING: The CSS selectors from upstream/main DO NOT EXIST in Bright Data HTML!")
        print("This confirms that these selectors only work with the standard Google Flights HTML,")
        print("not with the HTML returned by the Bright Data proxy.")

if __name__ == "__main__":
    main()