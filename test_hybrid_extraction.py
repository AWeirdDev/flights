#!/usr/bin/env python3
"""
Test the dev branch extraction with hybrid mode
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

def test_extraction(html_file):
    """Test extraction on a single HTML file"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Create mock response
    response = MockResponse(html_content)
    
    results = {}
    
    # Test both HTML and hybrid modes
    for mode in ['html', 'hybrid']:
        try:
            result = parse_response(response, mode)
            
            # Count fields
            field_counts = {
                'arrival_time_ahead': 0,
                'delay': 0,
                'operated_by': 0,
                'terminal_info': 0,
                'alliance': 0,
                'on_time_performance': 0
            }
            
            field_samples = {field: [] for field in field_counts}
            
            for flight in result.flights:
                if flight.arrival_time_ahead and flight.arrival_time_ahead.strip():
                    field_counts['arrival_time_ahead'] += 1
                    if len(field_samples['arrival_time_ahead']) < 3:
                        field_samples['arrival_time_ahead'].append(flight.arrival_time_ahead)
                
                if flight.delay:
                    field_counts['delay'] += 1
                    if len(field_samples['delay']) < 3:
                        field_samples['delay'].append(flight.delay)
                
                if hasattr(flight, 'operated_by') and flight.operated_by:
                    field_counts['operated_by'] += 1
                    if len(field_samples['operated_by']) < 3:
                        field_samples['operated_by'].append(flight.operated_by)
                        
                if hasattr(flight, 'terminal_info') and flight.terminal_info:
                    field_counts['terminal_info'] += 1
                    if len(field_samples['terminal_info']) < 3:
                        field_samples['terminal_info'].append(flight.terminal_info)
                        
                if hasattr(flight, 'alliance') and flight.alliance:
                    field_counts['alliance'] += 1
                    if len(field_samples['alliance']) < 3:
                        field_samples['alliance'].append(flight.alliance)
                        
                if hasattr(flight, 'on_time_performance') and flight.on_time_performance:
                    field_counts['on_time_performance'] += 1
                    if len(field_samples['on_time_performance']) < 3:
                        field_samples['on_time_performance'].append(flight.on_time_performance)
            
            results[mode] = {
                'success': True,
                'total_flights': len(result.flights),
                'field_counts': field_counts,
                'field_samples': field_samples
            }
        except Exception as e:
            results[mode] = {
                'success': False,
                'error': str(e)
            }
    
    return results

def main():
    """Test extraction on multiple HTML files"""
    print("TESTING DEV BRANCH EXTRACTION (HTML vs HYBRID modes)")
    print("=" * 70)
    
    # Find HTML files
    html_files = glob.glob('extreme_html_*.html')
    if not html_files:
        html_files = glob.glob('raw_html_*.html')
    
    if not html_files:
        print("No HTML files found.")
        return
    
    # Test just a few files to compare modes
    test_files = html_files[:3]
    print(f"Testing {len(test_files)} HTML files\n")
    
    for i, html_file in enumerate(test_files):
        print(f"\nFile {i+1}: {os.path.basename(html_file)}")
        print("=" * 50)
        
        results = test_extraction(html_file)
        
        for mode in ['html', 'hybrid']:
            print(f"\n{mode.upper()} MODE:")
            print("-" * 30)
            
            result = results[mode]
            if result['success']:
                print(f"Flights extracted: {result['total_flights']}")
                
                # Show field coverage
                print("\nField coverage:")
                for field, count in result['field_counts'].items():
                    if result['total_flights'] > 0:
                        percentage = (count / result['total_flights']) * 100
                        if count > 0:
                            print(f"  {field}: {count}/{result['total_flights']} ({percentage:.1f}%)")
                            if result['field_samples'][field]:
                                print(f"    Samples: {result['field_samples'][field][:2]}")
            else:
                print(f"Error: {result['error']}")
    
    print(f"\n{'='*70}")
    print("COMPARISON SUMMARY")
    print(f"{'='*70}")
    print("HTML mode: Uses CSS selectors directly on HTML")
    print("HYBRID mode: Uses JS data + HTML enrichments (includes operated_by from aria-labels)")

if __name__ == "__main__":
    main()