#!/usr/bin/env python3.11
"""Test script to reproduce the airport name/code issue"""

import json
from fast_flights.decoder import FlightDecoder, NLData, Flight

# Simulate two different flight data structures
# One with correct airport codes, one with airport names in the wrong place

# Correct data (airport code in position 3)
correct_flight_data = [
    None,  # 0
    None,  # 1
    "United Airlines",  # 2 - operator
    "IAH",  # 3 - departure_airport (code) - CORRECT
    "George Bush Intercontinental Airport",  # 4 - departure_airport_name
    "YUL",  # 5 - arrival_airport (code) - CORRECT
    "Montréal-Pierre Elliott Trudeau International Airport",  # 6 - arrival_airport_name
    None,  # 7
    [10, 0],  # 8 - departure_time
    None,  # 9
    [15, 1],  # 10 - arrival_time
    301,  # 11 - travel_time (minutes)
    None,  # 12
    None,  # 13
    "Average legroom (31 in)",  # 14 - seat_pitch_short
    None,  # 15
    None,  # 16
    "Boeing 737MAX 8 Passenger",  # 17 - aircraft
    None,  # 18
    None,  # 19
    [2025, 7, 15],  # 20 - departure_date
    [2025, 7, 15],  # 21 - arrival_date
    ["AC", "582", None, "Air Canada"],  # 22 - airline info [code, flight_number, ?, name]
]

# Incorrect data (airport name in position 3)
incorrect_flight_data = [
    None,  # 0
    None,  # 1
    "Air Canada",  # 2 - operator
    "George Bush Intercontinental Airport",  # 3 - WRONG: This should be "IAH"
    "George Bush Intercontinental Airport",  # 4 - departure_airport_name
    "Montréal-Pierre Elliott Trudeau International Airport",  # 5 - WRONG: This should be "YUL"
    "Montréal-Pierre Elliott Trudeau International Airport",  # 6 - arrival_airport_name
    None,  # 7
    [10, 0],  # 8 - departure_time
    None,  # 9
    [15, 1],  # 10 - arrival_time
    241,  # 11 - travel_time (minutes)
    None,  # 12
    None,  # 13
    "Average legroom (31 in)",  # 14 - seat_pitch_short
    None,  # 15
    None,  # 16
    "Boeing 737MAX 8 Passenger",  # 17 - aircraft
    None,  # 18
    None,  # 19
    [2025, 7, 15],  # 20 - departure_date
    [2025, 7, 15],  # 21 - arrival_date
    ["AC", "582", None, "Air Canada"],  # 22 - airline info [code, flight_number, ?, name]
]

def test_decoder():
    print("Testing FlightDecoder with correct data:")
    correct_nl = NLData(correct_flight_data)
    correct_decoded = FlightDecoder.decode_el(correct_nl)
    
    print(f"\nCorrect decoded flight:")
    print(f"  departure_airport: {correct_decoded.get('departure_airport')!r}")
    print(f"  departure_airport_name: {correct_decoded.get('departure_airport_name')!r}")
    print(f"  arrival_airport: {correct_decoded.get('arrival_airport')!r}")
    print(f"  arrival_airport_name: {correct_decoded.get('arrival_airport_name')!r}")
    
    print("\n" + "="*60)
    print("\nTesting FlightDecoder with incorrect data (airport names in code positions):")
    incorrect_nl = NLData(incorrect_flight_data)
    incorrect_decoded = FlightDecoder.decode_el(incorrect_nl)
    
    print(f"\nIncorrect decoded flight:")
    print(f"  departure_airport: {incorrect_decoded.get('departure_airport')!r}")
    print(f"  departure_airport_name: {incorrect_decoded.get('departure_airport_name')!r}")
    print(f"  arrival_airport: {incorrect_decoded.get('arrival_airport')!r}")
    print(f"  arrival_airport_name: {incorrect_decoded.get('arrival_airport_name')!r}")
    
    # Create Flight objects to see the issue
    print("\n" + "="*60)
    print("\nCreating Flight objects...")
    
    try:
        correct_flight = Flight(**{k: v for k, v in correct_decoded.items() if v is not None})
        print(f"\nCorrect Flight object created:")
        print(f"  departure_airport: {correct_flight.departure_airport!r}")
        print(f"  arrival_airport: {correct_flight.arrival_airport!r}")
    except Exception as e:
        print(f"\nError creating correct flight: {e}")
    
    try:
        incorrect_flight = Flight(**{k: v for k, v in incorrect_decoded.items() if v is not None})
        print(f"\nIncorrect Flight object created:")
        print(f"  departure_airport: {incorrect_flight.departure_airport!r}")
        print(f"  arrival_airport: {incorrect_flight.arrival_airport!r}")
        
        # This is the issue - airport names instead of codes!
        if len(incorrect_flight.departure_airport) > 4:
            print(f"\n⚠️  ISSUE FOUND: departure_airport contains full name instead of code!")
        if len(incorrect_flight.arrival_airport) > 4:
            print(f"⚠️  ISSUE FOUND: arrival_airport contains full name instead of code!")
            
    except Exception as e:
        print(f"\nError creating incorrect flight: {e}")

if __name__ == "__main__":
    test_decoder()