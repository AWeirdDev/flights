#!/usr/bin/env python3
"""
Test the dev branch extraction after adding arrival_time_ahead
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
    
    try:
        # Test HTML parser
        result = parse_response(response, 'html')
        
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
        
        return {
            'success': True,
            'total_flights': len(result.flights),
            'field_counts': field_counts,
            'field_samples': field_samples
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Test extraction on multiple HTML files"""
    print("TESTING DEV BRANCH EXTRACTION (WITH arrival_time_ahead)")
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
        'arrival_time_ahead': 0,
        'delay': 0,
        'operated_by': 0,
        'terminal_info': 0,
        'alliance': 0,
        'on_time_performance': 0
    }
    files_with_time_ahead = 0
    files_with_delay = 0
    files_with_operated_by = 0
    
    # Test first 10 files
    for i, html_file in enumerate(html_files[:10]):
        print(f"\nFile {i+1}: {os.path.basename(html_file)}")
        print("-" * 50)
        
        result = test_extraction(html_file)
        
        if result['success']:
            print(f"Flights extracted: {result['total_flights']}")
            total_flights += result['total_flights']
            
            # Update global counts
            for field in global_field_counts:
                global_field_counts[field] += result['field_counts'][field]
                
            if result['field_counts']['arrival_time_ahead'] > 0:
                files_with_time_ahead += 1
            if result['field_counts']['delay'] > 0:
                files_with_delay += 1
            if result['field_counts']['operated_by'] > 0:
                files_with_operated_by += 1
            
            # Show field coverage
            print("\nField coverage:")
            for field, count in result['field_counts'].items():
                if result['total_flights'] > 0:
                    percentage = (count / result['total_flights']) * 100
                    print(f"  {field}: {count}/{result['total_flights']} ({percentage:.1f}%)")
                    if result['field_samples'][field]:
                        print(f"    Samples: {result['field_samples'][field]}")
        else:
            print(f"Error: {result['error']}")
    
    # Overall summary
    print(f"\n{'='*70}")
    print("OVERALL SUMMARY")
    print(f"{'='*70}")
    print(f"Total flights extracted: {total_flights}")
    print(f"Files with arrival_time_ahead data: {files_with_time_ahead}/10")
    print(f"Files with delay data: {files_with_delay}/10")
    print(f"Files with operated_by data: {files_with_operated_by}/10")
    
    print("\nGlobal field coverage:")
    for field, count in global_field_counts.items():
        if total_flights > 0:
            percentage = (count / total_flights) * 100
            print(f"  {field}: {count}/{total_flights} ({percentage:.1f}%)")
    
    print(f"\n🔍 KEY FINDINGS:")
    if global_field_counts['arrival_time_ahead'] > 0:
        print(f"✅ ARRIVAL_TIME_AHEAD is now extractable! Found in {files_with_time_ahead}/10 files")
    else:
        print("❌ ARRIVAL_TIME_AHEAD not found")
        
    if global_field_counts['delay'] > 0:
        print(f"✅ DELAY is extractable! Found in {files_with_delay}/10 files")
    else:
        print("❌ DELAY not found (keeping it as requested)")
        
    if global_field_counts['operated_by'] > 0:
        print(f"✅ OPERATED_BY is extractable! Found in {files_with_operated_by}/10 files")
    else:
        print("❌ OPERATED_BY not found")

if __name__ == "__main__":
    main()