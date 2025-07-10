#!/usr/bin/env python3
"""
Extreme edge case testing with 80+ routes executed in maximum parallel
to find delay, terminal_info, alliance, and on_time_performance fields
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

# Comprehensive extreme edge case routes (80+ routes)
extreme_routes = [
    # Weather-Prone Routes (12 routes)
    {
        "name": "ORD→BOS (Winter Storm Corridor)",
        "route": [FlightData(date="2025-01-15", from_airport="ORD", to_airport="BOS")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "BUF→LGA (Snow Belt)",
        "route": [FlightData(date="2025-02-01", from_airport="BUF", to_airport="LGA")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "DEN→MSP (Snow Corridor)",
        "route": [FlightData(date="2025-01-20", from_airport="DEN", to_airport="MSP")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "BOS→DCA (Ice Storm Route)",
        "route": [FlightData(date="2025-02-10", from_airport="BOS", to_airport="DCA")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "MIA→JFK (Hurricane Season)",
        "route": [FlightData(date="2025-09-15", from_airport="MIA", to_airport="JFK")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "MCO→LGA (Summer Storms)",
        "route": [FlightData(date="2025-08-20", from_airport="MCO", to_airport="LGA")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "IAH→ATL (Hurricane Belt)",
        "route": [FlightData(date="2025-09-01", from_airport="IAH", to_airport="ATL")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "FLL→LGA (Hurricane Escape)",
        "route": [FlightData(date="2025-08-30", from_airport="FLL", to_airport="LGA")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "SFO→LAX (Fog Route)",
        "route": [FlightData(date="2025-12-15", from_airport="SFO", to_airport="LAX")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "PDX→SEA (Pacific Fog)",
        "route": [FlightData(date="2025-11-10", from_airport="PDX", to_airport="SEA")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "LHR→CDG (European Fog)",
        "route": [FlightData(date="2025-12-01", from_airport="LHR", to_airport="CDG")],
        "category": "weather_prone",
        "target_fields": ["delay", "terminal_info"]
    },
    {
        "name": "SFO→SAN (CA Fog Corridor)",
        "route": [FlightData(date="2025-11-20", from_airport="SFO", to_airport="SAN")],
        "category": "weather_prone",
        "target_fields": ["delay", "on_time_performance"]
    },

    # Notoriously Delayed Airports (15 routes)
    {
        "name": "LGA→ORD (Worst Delay Route)",
        "route": [FlightData(date="2025-08-25", from_airport="LGA", to_airport="ORD")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "LGA→BOS (Monday Morning)",
        "route": [FlightData(date="2025-08-25", from_airport="LGA", to_airport="BOS")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "LGA→DCA (Business Rush)",
        "route": [FlightData(date="2025-08-25", from_airport="LGA", to_airport="DCA")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "LGA→ATL (High Traffic)",
        "route": [FlightData(date="2025-08-25", from_airport="LGA", to_airport="ATL")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "LGA→MIA (Busy Route)",
        "route": [FlightData(date="2025-08-25", from_airport="LGA", to_airport="MIA")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "EWR→BOS (Congested)",
        "route": [FlightData(date="2025-08-22", from_airport="EWR", to_airport="BOS")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "EWR→DCA (Friday Evening)",
        "route": [FlightData(date="2025-08-22", from_airport="EWR", to_airport="DCA")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "EWR→ORD (Weather Hub)",
        "route": [FlightData(date="2025-08-22", from_airport="EWR", to_airport="ORD")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "EWR→MIA (Peak Summer)",
        "route": [FlightData(date="2025-08-22", from_airport="EWR", to_airport="MIA")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "EWR→LAX (Cross Country)",
        "route": [FlightData(date="2025-08-22", from_airport="EWR", to_airport="LAX")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→LGA (Weather to Congestion)",
        "route": [FlightData(date="2025-08-20", from_airport="ORD", to_airport="LGA")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→BOS (Storm Corridor)",
        "route": [FlightData(date="2025-08-20", from_airport="ORD", to_airport="BOS")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→DCA (Business Route)",
        "route": [FlightData(date="2025-08-20", from_airport="ORD", to_airport="DCA")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→EWR (Hub to Hub Chaos)",
        "route": [FlightData(date="2025-08-20", from_airport="ORD", to_airport="EWR")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→LAX (Cross Country)",
        "route": [FlightData(date="2025-08-20", from_airport="ORD", to_airport="LAX")],
        "category": "delay_prone",
        "target_fields": ["delay", "on_time_performance"]
    },

    # Multi-Terminal Airports (12 routes)
    {
        "name": "JFK→LAX (Terminal Heavy)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="LAX")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "delay"]
    },
    {
        "name": "JFK→SFO (Cross Country Premium)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="SFO")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "delay"]
    },
    {
        "name": "JFK→MIA (Domestic Hub)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="MIA")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "delay"]
    },
    {
        "name": "JFK→LHR (International Terminal)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="LHR")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "alliance"]
    },
    {
        "name": "JFK→CDG (International Hub)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="CDG")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "alliance"]
    },
    {
        "name": "JFK→NRT (Long Haul)",
        "route": [FlightData(date="2025-08-15", from_airport="JFK", to_airport="NRT")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "alliance"]
    },
    {
        "name": "LAX→JFK (9 Terminals)",
        "route": [FlightData(date="2025-08-16", from_airport="LAX", to_airport="JFK")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "delay"]
    },
    {
        "name": "LAX→ORD (Major Hub)",
        "route": [FlightData(date="2025-08-16", from_airport="LAX", to_airport="ORD")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "delay"]
    },
    {
        "name": "LAX→NRT (Pacific Route)",
        "route": [FlightData(date="2025-08-16", from_airport="LAX", to_airport="NRT")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "alliance"]
    },
    {
        "name": "LAX→LHR (Premium International)",
        "route": [FlightData(date="2025-08-16", from_airport="LAX", to_airport="LHR")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "alliance"]
    },
    {
        "name": "LAX→SFO (California Corridor)",
        "route": [FlightData(date="2025-08-16", from_airport="LAX", to_airport="SFO")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "on_time_performance"]
    },
    {
        "name": "LAX→DFW (Hub to Hub)",
        "route": [FlightData(date="2025-08-16", from_airport="LAX", to_airport="DFW")],
        "category": "multi_terminal",
        "target_fields": ["terminal_info", "delay"]
    },

    # Alliance-Heavy International Routes (12 routes)
    {
        "name": "SFO→FRA (Star Alliance Hub)",
        "route": [FlightData(date="2025-08-17", from_airport="SFO", to_airport="FRA")],
        "category": "star_alliance",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "ORD→FRA (United/Lufthansa)",
        "route": [FlightData(date="2025-08-17", from_airport="ORD", to_airport="FRA")],
        "category": "star_alliance",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "YYZ→FRA (Air Canada/Lufthansa)",
        "route": [FlightData(date="2025-08-17", from_airport="YYZ", to_airport="FRA")],
        "category": "star_alliance",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "NRT→FRA (ANA/Lufthansa)",
        "route": [FlightData(date="2025-08-17", from_airport="NRT", to_airport="FRA")],
        "category": "star_alliance",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "IAD→FRA (United Hub)",
        "route": [FlightData(date="2025-08-17", from_airport="IAD", to_airport="FRA")],
        "category": "star_alliance",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "LAX→FRA (Star Alliance Route)",
        "route": [FlightData(date="2025-08-17", from_airport="LAX", to_airport="FRA")],
        "category": "star_alliance",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "DFW→LHR (American/BA oneworld)",
        "route": [FlightData(date="2025-08-18", from_airport="DFW", to_airport="LHR")],
        "category": "oneworld",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "LAX→LHR (oneworld Pacific)",
        "route": [FlightData(date="2025-08-18", from_airport="LAX", to_airport="LHR")],
        "category": "oneworld",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "MIA→LHR (AA/BA Alliance)",
        "route": [FlightData(date="2025-08-18", from_airport="MIA", to_airport="LHR")],
        "category": "oneworld",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "ORD→LHR (oneworld Hub)",
        "route": [FlightData(date="2025-08-18", from_airport="ORD", to_airport="LHR")],
        "category": "oneworld",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "JFK→CDG (SkyTeam Hub)",
        "route": [FlightData(date="2025-08-19", from_airport="JFK", to_airport="CDG")],
        "category": "skyteam",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "ATL→CDG (Delta/Air France)",
        "route": [FlightData(date="2025-08-19", from_airport="ATL", to_airport="CDG")],
        "category": "skyteam",
        "target_fields": ["alliance", "terminal_info"]
    },

    # Peak Travel Dates (10 routes) 
    {
        "name": "LGA→ATL (Thanksgiving Eve)",
        "route": [FlightData(date="2025-11-26", from_airport="LGA", to_airport="ATL")],
        "category": "peak_travel",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→LAX (Thanksgiving Wed)",
        "route": [FlightData(date="2025-11-26", from_airport="ORD", to_airport="LAX")],
        "category": "peak_travel",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "JFK→MIA (Thanksgiving Travel)",
        "route": [FlightData(date="2025-11-27", from_airport="JFK", to_airport="MIA")],
        "category": "peak_travel",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "DFW→DEN (Holiday Rush)",
        "route": [FlightData(date="2025-11-27", from_airport="DFW", to_airport="DEN")],
        "category": "peak_travel",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "LAX→JFK (Christmas Week)",
        "route": [FlightData(date="2025-12-23", from_airport="LAX", to_airport="JFK")],
        "category": "peak_travel",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ATL→LGA (Christmas Eve)",
        "route": [FlightData(date="2025-12-24", from_airport="ATL", to_airport="LGA")],
        "category": "peak_travel",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→MIA (Holiday Escape)",
        "route": [FlightData(date="2025-12-27", from_airport="ORD", to_airport="MIA")],
        "category": "peak_travel",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "DFW→LAX (New Year's)",
        "route": [FlightData(date="2025-12-30", from_airport="DFW", to_airport="LAX")],
        "category": "peak_travel",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "JFK→LAX (July 4th Weekend)",
        "route": [FlightData(date="2025-07-04", from_airport="JFK", to_airport="LAX")],
        "category": "peak_travel",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "LAX→LHR (Summer Peak)",
        "route": [FlightData(date="2025-07-03", from_airport="LAX", to_airport="LHR")],
        "category": "peak_travel",
        "target_fields": ["delay", "terminal_info"]
    },

    # Red-Eye and Overnight Routes (8 routes)
    {
        "name": "LAX→JFK (Red-Eye)",
        "route": [FlightData(date="2025-08-20", from_airport="LAX", to_airport="JFK")],
        "category": "redeye",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "SFO→JFK (Late Night)",
        "route": [FlightData(date="2025-08-20", from_airport="SFO", to_airport="JFK")],
        "category": "redeye",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "LAX→BOS (Cross Country Red-Eye)",
        "route": [FlightData(date="2025-08-20", from_airport="LAX", to_airport="BOS")],
        "category": "redeye",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "SEA→JFK (Pacific Red-Eye)",
        "route": [FlightData(date="2025-08-20", from_airport="SEA", to_airport="JFK")],
        "category": "redeye",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "JFK→LHR (Overnight International)",
        "route": [FlightData(date="2025-08-20", from_airport="JFK", to_airport="LHR")],
        "category": "redeye",
        "target_fields": ["delay", "terminal_info"]
    },
    {
        "name": "LAX→NRT (Pacific Overnight)",
        "route": [FlightData(date="2025-08-20", from_airport="LAX", to_airport="NRT")],
        "category": "redeye",
        "target_fields": ["delay", "terminal_info"]
    },
    {
        "name": "SFO→NRT (Late Departure)",
        "route": [FlightData(date="2025-08-20", from_airport="SFO", to_airport="NRT")],
        "category": "redeye",
        "target_fields": ["delay", "terminal_info"]
    },
    {
        "name": "ORD→FRA (European Overnight)",
        "route": [FlightData(date="2025-08-20", from_airport="ORD", to_airport="FRA")],
        "category": "redeye",
        "target_fields": ["delay", "alliance"]
    },

    # Regional and Connecting Routes (6 routes)
    {
        "name": "ATL→GSP (Regional Hub)",
        "route": [FlightData(date="2025-08-21", from_airport="ATL", to_airport="GSP")],
        "category": "regional",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "DFW→ABI (Texas Regional)",
        "route": [FlightData(date="2025-08-21", from_airport="DFW", to_airport="ABI")],
        "category": "regional",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "ORD→GRR (Midwest Regional)",
        "route": [FlightData(date="2025-08-21", from_airport="ORD", to_airport="GRR")],
        "category": "regional",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "MSP→DLH (Northern Regional)",
        "route": [FlightData(date="2025-08-21", from_airport="MSP", to_airport="DLH")],
        "category": "regional",
        "target_fields": ["delay", "on_time_performance"]
    },
    {
        "name": "PWM→JFK (Small to Major)",
        "route": [FlightData(date="2025-08-21", from_airport="PWM", to_airport="JFK")],
        "category": "regional",
        "target_fields": ["delay", "terminal_info"]
    },
    {
        "name": "BGR→BOS (New England Regional)",
        "route": [FlightData(date="2025-08-21", from_airport="BGR", to_airport="BOS")],
        "category": "regional",
        "target_fields": ["delay", "on_time_performance"]
    },

    # Premium Cabin Focus (5 routes)
    {
        "name": "JFK→LHR (First Class Premium)",
        "route": [FlightData(date="2025-08-22", from_airport="JFK", to_airport="LHR")],
        "category": "premium",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "LAX→NRT (First Class Long-Haul)",
        "route": [FlightData(date="2025-08-22", from_airport="LAX", to_airport="NRT")],
        "category": "premium",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "SFO→FRA (Lufthansa Premium)",
        "route": [FlightData(date="2025-08-22", from_airport="SFO", to_airport="FRA")],
        "category": "premium",
        "target_fields": ["alliance", "terminal_info"]
    },
    {
        "name": "DCA→LGA (Business Shuttle)",
        "route": [FlightData(date="2025-08-22", from_airport="DCA", to_airport="LGA")],
        "category": "premium",
        "target_fields": ["on_time_performance", "delay"]
    },
    {
        "name": "BOS→DCA (Northeast Business)",
        "route": [FlightData(date="2025-08-22", from_airport="BOS", to_airport="DCA")],
        "category": "premium",
        "target_fields": ["on_time_performance", "delay"]
    }
]

def enhanced_keyword_search(html_content, route_name):
    """Enhanced keyword search with more patterns"""
    keywords = {
        'delay': [
            'delay', 'delayed', 'late', 'behind schedule', 'running late',
            'departure delay', 'arrival delay', 'min delay', 'hour delay', 'hrs delay',
            'delayed by', 'running behind', 'expected delay', 'delay expected',
            'weather delay', 'mechanical delay', 'air traffic delay'
        ],
        'terminal': [
            'terminal', 'gate', 'concourse', 'pier',
            'terminal 1', 'terminal 2', 'terminal 3', 'terminal 4', 'terminal 5',
            'terminal a', 'terminal b', 'terminal c', 'terminal d', 'terminal e',
            'gate a', 'gate b', 'gate c', 'concourse a', 'concourse b',
            'departure terminal', 'arrival terminal', 'terminal change'
        ],
        'alliance': [
            'alliance', 'star alliance', 'oneworld', 'skyteam', 'sky team',
            'member of', 'alliance member', 'alliance partner',
            'star alliance member', 'oneworld member', 'skyteam member'
        ],
        'on_time': [
            'on-time', 'on time', 'ontime', 'punctuality', 'reliability',
            '% on time', 'percent on time', 'on-time performance',
            'punctual', 'reliable', 'delay statistics', 'performance score'
        ]
    }
    
    findings = {}
    
    for category, terms in keywords.items():
        findings[category] = []
        for term in terms:
            # Case insensitive search with word boundaries
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(html_content)
            
            for match in matches:
                # Get more context around the match
                start = max(0, match.start() - 150)
                end = min(len(html_content), match.end() + 150)
                context = html_content[start:end]
                
                # Clean up the context
                context = ' '.join(context.split())
                
                findings[category].append({
                    'term': term,
                    'position': match.start(),
                    'context': context
                })
    
    return findings

def extract_all_aria_labels_comprehensive(html_content):
    """Extract all aria-labels with comprehensive analysis"""
    from selectolax.lexbor import LexborHTMLParser
    
    parser = LexborHTMLParser(html_content)
    
    # Get all elements with aria-label
    aria_elements = parser.css('*[aria-label]')
    
    aria_labels = []
    keyword_matches = []
    
    for elem in aria_elements:
        aria_label = elem.attributes.get('aria-label', '')
        if aria_label:
            aria_labels.append({
                'tag': elem.tag,
                'classes': elem.attributes.get('class', ''),
                'aria_label': aria_label
            })
            
            # Check for keywords in aria-labels
            keywords_found = []
            aria_lower = aria_label.lower()
            
            if any(word in aria_lower for word in ['delay', 'late', 'behind']):
                keywords_found.append('delay')
            if any(word in aria_lower for word in ['terminal', 'gate', 'concourse']):
                keywords_found.append('terminal')
            if any(word in aria_lower for word in ['alliance', 'oneworld', 'skyteam', 'star']):
                keywords_found.append('alliance')
            if any(word in aria_lower for word in ['on-time', 'on time', 'punctual', '%']):
                keywords_found.append('on_time')
            
            if keywords_found:
                keyword_matches.append({
                    'tag': elem.tag,
                    'classes': elem.attributes.get('class', ''),
                    'keywords': keywords_found,
                    'aria_label': aria_label
                })
    
    return aria_labels, keyword_matches

def analyze_fields_comprehensive(flights, route_name):
    """Comprehensive field analysis"""
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
        # Count non-null fields
        if flight.delay is not None:
            field_counts['delay'] += 1
            if len(field_samples['delay']) < 5:
                field_samples['delay'].append(flight.delay)
        
        if flight.operated_by is not None:
            field_counts['operated_by'] += 1
            if len(field_samples['operated_by']) < 5:
                field_samples['operated_by'].append(flight.operated_by)
        
        if flight.terminal_info is not None:
            field_counts['terminal_info'] += 1
            if len(field_samples['terminal_info']) < 5:
                field_samples['terminal_info'].append(flight.terminal_info)
        
        if flight.alliance is not None:
            field_counts['alliance'] += 1
            if len(field_samples['alliance']) < 5:
                field_samples['alliance'].append(flight.alliance)
        
        if flight.on_time_performance is not None:
            field_counts['on_time_performance'] += 1
            if len(field_samples['on_time_performance']) < 5:
                field_samples['on_time_performance'].append(flight.on_time_performance)
    
    return field_counts, field_samples, total_flights

def test_route_comprehensive(route_info):
    """Comprehensive route testing with enhanced analysis"""
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
        result = get_flights_from_filter(filter, mode="bright-data", data_source='hybrid')
        
        if not result or not result.flights:
            return {
                'name': route_info['name'],
                'category': route_info['category'],
                'target_fields': route_info['target_fields'],
                'success': False,
                'error': 'No flights found',
                'field_counts': None,
                'field_samples': None,
                'total_flights': 0,
                'keyword_findings': None,
                'aria_keyword_matches': None
            }
        
        # Get raw HTML for analysis
        from fast_flights.bright_data_fetch import bright_data_fetch
        data = filter.as_b64()
        params = {
            "tfs": data.decode("utf-8"),
            "hl": "en", 
            "tfu": "EgQIABABIgA",
            "curr": "",
        }
        raw_response = bright_data_fetch(params)
        
        # Enhanced keyword search
        keyword_findings = enhanced_keyword_search(raw_response.text, route_info['name'])
        
        # Comprehensive aria-label analysis
        aria_labels, aria_keyword_matches = extract_all_aria_labels_comprehensive(raw_response.text)
        
        # Analyze field availability
        field_counts, field_samples, total_flights = analyze_fields_comprehensive(result.flights, route_info['name'])
        
        # Save raw HTML if keywords found
        if any(len(findings) > 0 for findings in keyword_findings.values()) or aria_keyword_matches:
            filename = f"raw_html_extreme_{route_info['name'].replace('→', '_').replace(' ', '_').replace('(', '').replace(')', '')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(raw_response.text)
        
        return {
            'name': route_info['name'],
            'category': route_info['category'],
            'target_fields': route_info['target_fields'],
            'success': True,
            'error': None,
            'field_counts': field_counts,
            'field_samples': field_samples,
            'total_flights': total_flights,
            'current_price': result.current_price,
            'keyword_findings': keyword_findings,
            'aria_keyword_matches': aria_keyword_matches,
            'total_aria_labels': len(aria_labels)
        }
        
    except Exception as e:
        return {
            'name': route_info['name'],
            'category': route_info['category'],
            'target_fields': route_info['target_fields'],
            'success': False,
            'error': f"{type(e).__name__}: {e}",
            'field_counts': None,
            'field_samples': None,
            'total_flights': 0,
            'keyword_findings': None,
            'aria_keyword_matches': None
        }

def main():
    """Main testing function with controlled parallelization"""
    print("EXTREME EDGE CASE TESTING - CONTROLLED PARALLELIZATION")
    print("=" * 80)
    print(f"Testing {len(extreme_routes)} routes simultaneously")
    print("Target fields: delay, terminal_info, alliance, on_time_performance")
    print("Using controlled parallel execution (10 concurrent connections)")
    
    # Execute ALL routes with controlled parallelization
    print(f"\nExecuting all {len(extreme_routes)} routes with 10 concurrent connections...")
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks simultaneously
        future_to_route = {executor.submit(test_route_comprehensive, route_info): route_info for route_info in extreme_routes}
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_route):
            route_info = future_to_route[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1
                status = "✅" if result['success'] else "❌"
                print(f"{status} [{completed}/{len(extreme_routes)}] {result['name']}")
            except Exception as exc:
                completed += 1
                print(f"❌ [{completed}/{len(extreme_routes)}] {route_info['name']} - {exc}")
                results.append({
                    'name': route_info['name'],
                    'category': route_info['category'],
                    'target_fields': route_info['target_fields'],
                    'success': False,
                    'error': str(exc),
                    'field_counts': None,
                    'field_samples': None,
                    'total_flights': 0
                })
    
    # Analyze comprehensive results
    print(f"\n{'='*80}")
    print("COMPREHENSIVE EXTREME EDGE CASE ANALYSIS")
    print(f"{'='*80}")
    
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
    
    aria_keyword_discoveries = []
    
    successful_tests = 0
    total_flights_tested = 0
    total_keyword_matches = 0
    total_aria_keyword_matches = 0
    
    # Process all results
    for result in results:
        if result['success']:
            successful_tests += 1
            total_flights_tested += result['total_flights']
            
            # Check for field discoveries in parsed data
            for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance']:
                if result['field_counts'] and result['field_counts'][field] > 0:
                    field_discoveries[field].append({
                        'route': result['name'],
                        'category': result['category'],
                        'count': result['field_counts'][field],
                        'total': result['total_flights'],
                        'samples': result['field_samples'][field] if result['field_samples'] else []
                    })
            
            # Check for keyword discoveries in raw HTML
            if result['keyword_findings']:
                for category, findings in result['keyword_findings'].items():
                    if findings:
                        total_keyword_matches += len(findings)
                        keyword_discoveries[category].extend([{
                            'route': result['name'],
                            'category': result['category'],
                            'matches': len(findings),
                            'terms': list(set([f['term'] for f in findings]))
                        }])
            
            # Check for aria-label keyword discoveries
            if result['aria_keyword_matches']:
                total_aria_keyword_matches += len(result['aria_keyword_matches'])
                aria_keyword_discoveries.extend([{
                    'route': result['name'],
                    'category': result['category'],
                    'matches': result['aria_keyword_matches']
                }])
    
    # Report field discoveries
    print(f"\n🎯 FIELD DISCOVERIES IN PARSED DATA:")
    any_field_discoveries = False
    for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance']:
        if field_discoveries[field]:
            any_field_discoveries = True
            print(f"\n🎉 {field.upper()} FOUND IN PARSED DATA!")
            for disc in field_discoveries[field]:
                percentage = (disc['count'] / disc['total']) * 100
                print(f"  ✅ {disc['route']} ({disc['category']}): {disc['count']}/{disc['total']} ({percentage:.1f}%)")
                if disc['samples']:
                    print(f"     Examples: {disc['samples']}")
        else:
            print(f"\n❌ {field.upper()}: Not found in parsed data")
    
    # Report keyword discoveries
    print(f"\n🔍 KEYWORD DISCOVERIES IN RAW HTML:")
    any_keyword_discoveries = False
    for category in ['delay', 'terminal', 'alliance', 'on_time']:
        if keyword_discoveries[category]:
            any_keyword_discoveries = True
            print(f"\n🎯 {category.upper()} KEYWORDS FOUND!")
            for disc in keyword_discoveries[category]:
                print(f"  ⚠️  {disc['route']} ({disc['category']}): {disc['matches']} matches")
                print(f"     Terms: {disc['terms']}")
        else:
            print(f"\n❌ {category.upper()}: No keywords found")
    
    # Report aria-label discoveries
    print(f"\n🏷️  ARIA-LABEL KEYWORD DISCOVERIES:")
    if aria_keyword_discoveries:
        print(f"\n🎯 ARIA-LABEL KEYWORDS FOUND!")
        for disc in aria_keyword_discoveries:
            print(f"  ⚠️  {disc['route']} ({disc['category']}):")
            for match in disc['matches'][:3]:  # Show first 3
                print(f"     Keywords: {match['keywords']}")
                print(f"     Context: {match['aria_label'][:100]}...")
    else:
        print(f"\n❌ No keyword matches in aria-labels")
    
    # Statistical summary
    print(f"\n{'='*80}")
    print("EXTREME EDGE CASE SUMMARY")
    print(f"{'='*80}")
    print(f"Routes tested: {successful_tests}/{len(extreme_routes)}")
    print(f"Total flights analyzed: {total_flights_tested}")
    print(f"Total raw HTML keyword matches: {total_keyword_matches}")
    print(f"Total aria-label keyword matches: {total_aria_keyword_matches}")
    
    # Final conclusion
    if any_field_discoveries:
        found_fields = [field for field in ['delay', 'terminal_info', 'alliance', 'on_time_performance'] if field_discoveries[field]]
        print(f"\n🎉 BREAKTHROUGH: Found {len(found_fields)} field(s) in parsed data: {', '.join(found_fields)}")
    elif any_keyword_discoveries or aria_keyword_discoveries:
        print(f"\n⚠️  PARTIAL SUCCESS: Found keywords in raw HTML but not in parsed data")
        print(f"This suggests extraction logic needs refinement")
    else:
        print(f"\n❌ NO DISCOVERIES: Fields not found in {len(extreme_routes)} extreme edge cases")
        print(f"Definitive proof that these fields are not available in Google Flights API")
    
    print(f"\nExtreme edge case testing complete.")

if __name__ == "__main__":
    main()