#!/usr/bin/env python3
"""
Analyze the specific contexts where keywords appear in raw HTML
Focus on flight data sections vs CSS/JavaScript sections
"""

import os
import re
from selectolax.lexbor import LexborHTMLParser

def analyze_alliance_data():
    """Analyze alliance data found in the HTML"""
    print("ALLIANCE DATA ANALYSIS")
    print("=" * 50)
    
    # Read one of the HTML files
    with open("raw_html_DFW-LHR-oneworld.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Find the alliance data structure
    alliance_pattern = r'\["ONEWORLD","Oneworld"\],\["SKYTEAM","SkyTeam"\],\["STAR_ALLIANCE","Star Alliance"\]'
    matches = list(re.finditer(alliance_pattern, html_content))
    
    for match in matches:
        start = max(0, match.start() - 500)
        end = min(len(html_content), match.end() + 500)
        context = html_content[start:end]
        
        print(f"Alliance data found at position {match.start()}:")
        print(f"Context: {context}")
        print("-" * 50)
    
    # Look for airline codes associated with alliances
    airline_alliance_pattern = r'\["[A-Z0-9]+","[^"]+"\].*(?:ONEWORLD|SKYTEAM|STAR_ALLIANCE)'
    matches = list(re.finditer(airline_alliance_pattern, html_content, re.IGNORECASE))
    
    print(f"\nAIRLINE-ALLIANCE ASSOCIATIONS:")
    for i, match in enumerate(matches):
        if i >= 5:  # Show first 5
            break
        print(f"  {match.group(0)}")

def analyze_delay_contexts():
    """Analyze where delay-related keywords appear"""
    print("\nDELAY CONTEXT ANALYSIS")
    print("=" * 50)
    
    # Read one of the HTML files
    with open("raw_html_ORD-LGA-delay-prone.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Look for delay in different contexts
    delay_patterns = [
        r'delay[^a-zA-Z][^}]*?(?:min|hour|hrs?)',  # delay with time units
        r'delayed?[^a-zA-Z][^}]*?(?:min|hour|hrs?)',  # delayed with time units  
        r'(?:departure|arrival)[^}]*?delay',  # departure/arrival delay
        r'delay[^}]*?(?:departure|arrival)',  # delay departure/arrival
    ]
    
    for pattern in delay_patterns:
        matches = list(re.finditer(pattern, html_content, re.IGNORECASE))
        
        print(f"\nPattern: {pattern}")
        print(f"Found {len(matches)} matches")
        
        for i, match in enumerate(matches):
            if i >= 3:  # Show first 3 matches
                break
            start = max(0, match.start() - 100)
            end = min(len(html_content), match.end() + 100)
            context = html_content[start:end]
            context = ' '.join(context.split())  # Clean up whitespace
            print(f"  Match {i+1}: {context}")
        
        if len(matches) == 0:
            print("  No matches found")
        elif len(matches) > 3:
            print(f"  ... and {len(matches) - 3} more matches")

def analyze_terminal_contexts():
    """Analyze where terminal-related keywords appear"""
    print("\nTERMINAL CONTEXT ANALYSIS")
    print("=" * 50)
    
    # Read one of the HTML files
    with open("raw_html_JFK-NRT-long-haul.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Look for terminal in different contexts
    terminal_patterns = [
        r'terminal\s*[0-9A-Z]',  # terminal with number/letter
        r'terminal[^a-zA-Z][^}]*?(?:departure|arrival)',  # terminal with departure/arrival
        r'(?:departure|arrival)[^}]*?terminal',  # departure/arrival terminal
    ]
    
    for pattern in terminal_patterns:
        matches = list(re.finditer(pattern, html_content, re.IGNORECASE))
        
        print(f"\nPattern: {pattern}")
        print(f"Found {len(matches)} matches")
        
        for i, match in enumerate(matches):
            if i >= 3:  # Show first 3 matches
                break
            start = max(0, match.start() - 100)
            end = min(len(html_content), match.end() + 100)
            context = html_content[start:end]
            context = ' '.join(context.split())  # Clean up whitespace
            print(f"  Match {i+1}: {context}")
        
        if len(matches) == 0:
            print("  No matches found")
        elif len(matches) > 3:
            print(f"  ... and {len(matches) - 3} more matches")

def analyze_flight_aria_labels():
    """Analyze aria-labels specifically in flight items"""
    print("\nFLIGHT ARIA-LABEL ANALYSIS")
    print("=" * 50)
    
    # Read one of the HTML files
    with open("raw_html_JFK-LAX-domestic.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    parser = LexborHTMLParser(html_content)
    
    # Get flight containers
    flight_containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
    
    print(f"Found {len(flight_containers)} flight containers")
    
    # Analyze first container in detail
    if flight_containers:
        container = flight_containers[0]
        flight_items = container.css("ul.Rk10dc li")
        
        print(f"First container has {len(flight_items)} flight items")
        
        # Look at first few items
        for i, item in enumerate(flight_items[:3]):
            print(f"\nFlight item {i+1}:")
            
            # Get all aria-labels within this item
            aria_elements = item.css('*[aria-label]')
            print(f"  Found {len(aria_elements)} elements with aria-label")
            
            for j, elem in enumerate(aria_elements):
                aria_label = elem.attributes.get('aria-label', '')
                if aria_label:
                    # Check if aria-label contains keywords
                    keywords_found = []
                    if 'delay' in aria_label.lower():
                        keywords_found.append('delay')
                    if 'terminal' in aria_label.lower():
                        keywords_found.append('terminal')
                    if any(alliance in aria_label.lower() for alliance in ['alliance', 'oneworld', 'skyteam', 'star']):
                        keywords_found.append('alliance')
                    if 'on-time' in aria_label.lower() or 'on time' in aria_label.lower():
                        keywords_found.append('on-time')
                    
                    if keywords_found:
                        print(f"    Element {j+1} ({elem.tag}, {elem.attributes.get('class', '')}): {keywords_found}")
                        print(f"      Aria-label: {aria_label[:200]}...")
                    elif j < 3:  # Show first 3 regardless
                        print(f"    Element {j+1} ({elem.tag}, {elem.attributes.get('class', '')}): No keywords")
                        print(f"      Aria-label: {aria_label[:100]}...")

def check_javascript_data():
    """Check if the keywords are in JavaScript data structures"""
    print("\nJAVASCRIPT DATA ANALYSIS")
    print("=" * 50)
    
    # Read one of the HTML files
    with open("raw_html_SFO-FRA-international.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Look for JavaScript data that might contain flight information
    script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL)
    
    print(f"Found {len(script_tags)} script tags")
    
    # Look for data structures that might contain flight info
    for i, script in enumerate(script_tags):
        if 'ONEWORLD' in script or 'SKYTEAM' in script or 'STAR_ALLIANCE' in script:
            print(f"\nScript {i+1} contains alliance data:")
            
            # Extract just the alliance-related parts
            alliance_matches = list(re.finditer(r'[^"]*(?:ONEWORLD|SKYTEAM|STAR_ALLIANCE)[^"]*', script))
            for match in alliance_matches:
                start = max(0, match.start() - 200)
                end = min(len(script), match.end() + 200)
                context = script[start:end]
                print(f"  {context}")
                break  # Just show first match per script

def main():
    """Main analysis function"""
    print("KEYWORD CONTEXT ANALYSIS")
    print("=" * 70)
    print("Analyzing WHERE keywords appear in the raw HTML")
    
    # Check if HTML files exist
    html_files = [
        "raw_html_JFK-LAX-domestic.html",
        "raw_html_DFW-LHR-oneworld.html", 
        "raw_html_ORD-LGA-delay-prone.html",
        "raw_html_JFK-NRT-long-haul.html",
        "raw_html_SFO-FRA-international.html"
    ]
    
    missing_files = [f for f in html_files if not os.path.exists(f)]
    if missing_files:
        print(f"Missing HTML files: {missing_files}")
        print("Please run debug_raw_html.py first")
        return
    
    # Run analyses
    analyze_alliance_data()
    analyze_delay_contexts()
    analyze_terminal_contexts()
    analyze_flight_aria_labels()
    check_javascript_data()
    
    print(f"\n{'='*70}")
    print("ANALYSIS CONCLUSIONS")
    print(f"{'='*70}")
    print("Based on this analysis, we can determine:")
    print("1. Whether keywords are in flight data or just CSS/JavaScript")
    print("2. The exact format/structure of the data")
    print("3. How to update extraction patterns to find this information")

if __name__ == "__main__":
    main()