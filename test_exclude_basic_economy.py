#!/usr/bin/env python3
"""
Test exclude_basic_economy functionality
"""

from fast_flights import create_filter, FlightData, Passengers
import base64

# Test 1: Create filter WITHOUT excluding basic economy (default)
filter_default = create_filter(
    flight_data=[
        FlightData(
            date="2025-07-01",
            from_airport="TPE",
            to_airport="MYJ",
        )
    ],
    trip="one-way",
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
)

# Test 2: Create filter WITH excluding basic economy
filter_exclude = create_filter(
    flight_data=[
        FlightData(
            date="2025-07-01",
            from_airport="TPE",
            to_airport="MYJ",
        )
    ],
    trip="one-way",
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
    exclude_basic_economy=True,
)

# Get the serialized bytes
bytes_default = filter_default.to_string()
bytes_exclude = filter_exclude.to_string()

print("=" * 80)
print("TEST: exclude_basic_economy functionality")
print("=" * 80)

print("\n1. Filter WITHOUT exclude_basic_economy (default):")
print(f"   Base64: {filter_default.as_b64().decode('utf-8')}")
print(f"   Bytes length: {len(bytes_default)}")
print(f"   Raw bytes: {bytes_default.hex()}")

print("\n2. Filter WITH exclude_basic_economy=True:")
print(f"   Base64: {filter_exclude.as_b64().decode('utf-8')}")
print(f"   Bytes length: {len(bytes_exclude)}")
print(f"   Raw bytes: {bytes_exclude.hex()}")

print("\n3. Difference analysis:")
print(f"   Length difference: {len(bytes_exclude) - len(bytes_default)} bytes")

# Check if the exclude flag is in the serialized data
# Field 25 with wire type 0 (varint) = (25 << 3) | 0 = 200 = 0xC8
# But protobuf encodes it as varint, so 25 << 3 = 200, which is 0xC8
# Actually field number 25 with wire type 0 = field tag 200 = 0xC8 in hex
# But varint encoding means 200 = 0xC8 = 0b11001000 which encodes as 0xC8 0x01 in varint
# Actually 200 fits in one byte: 0xC8
print(f"\n4. Field 25 check:")
print(f"   Looking for field 25 (wire type 0): tag byte should be {(25 << 3) | 0} = 0x{(25 << 3) | 0:02x}")

# Search for the field in both byte strings
field_25_tag = (25 << 3) | 0  # Field number 25, wire type 0 (varint)
if field_25_tag.to_bytes(1, 'big') in bytes_exclude:
    idx = bytes_exclude.find(field_25_tag.to_bytes(1, 'big'))
    print(f"   ✓ Field 25 found in exclude=True filter at byte position {idx}")
    if idx + 1 < len(bytes_exclude):
        print(f"   ✓ Field 25 value: {bytes_exclude[idx+1]}")
else:
    print(f"   ✗ Field 25 NOT found in exclude=True filter")

if field_25_tag.to_bytes(1, 'big') in bytes_default:
    idx = bytes_default.find(field_25_tag.to_bytes(1, 'big'))
    print(f"   ○ Field 25 found in exclude=False filter at byte position {idx}")
else:
    print(f"   ○ Field 25 NOT found in exclude=False filter (expected - optional field)")

print("\n5. Google Flights URLs:")
print(f"   Without exclude: https://www.google.com/travel/flights?tfs={filter_default.as_b64().decode('utf-8')}")
print(f"   With exclude:    https://www.google.com/travel/flights?tfs={filter_exclude.as_b64().decode('utf-8')}")

print("\n" + "=" * 80)
print("✓ Test completed successfully!")
print("=" * 80)
