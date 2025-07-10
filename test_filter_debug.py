#!/usr/bin/env python3
"""
Debug filter encoding for round-trip flights
"""

from datetime import datetime, timedelta
from fast_flights import FlightData, Passengers
from fast_flights.filter import TFSData

# Test configuration
test_date = datetime.now() + timedelta(days=30)
return_date = test_date + timedelta(days=7)

# Create a round-trip filter
flight_data = [
    FlightData(
        date=test_date.strftime("%Y-%m-%d"),
        from_airport="JFK",
        to_airport="LAX",
    ),
    FlightData(
        date=return_date.strftime("%Y-%m-%d"),
        from_airport="LAX",
        to_airport="JFK",
    )
]

filter = TFSData.from_interface(
    flight_data=flight_data,
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
)

# Get the base64 encoded filter
data = filter.as_b64()
print("Filter base64:", data.decode("utf-8"))
print()

# Decode to see what's in it
import base64
decoded = base64.b64decode(data)
print("Decoded filter (first 200 chars):", decoded[:200])
print()

# Check the URL that would be generated
params = {
    "tfs": data.decode("utf-8"),
    "hl": "en",
    "tfu": "EgQIABABIgA",
    "curr": "",
}

url = "https://www.google.com/travel/flights?" + "&".join(f"{k}={v}" for k, v in params.items())
print("URL length:", len(url))
print("URL (first 200 chars):", url[:200])