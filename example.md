# Fast Flights - Code Examples

This guide shows how to use `fast-flights` to search for flights and retrieve detailed flight information, including complete roundtrip booking workflows with support for both direct and connecting flights.

## Prerequisites

```bash
pip install fast-flights
```

## Example 1: One-Way Flight with Detailed Information

Search for a one-way flight excluding basic economy fares, and get detailed flight information including flight numbers.

```python
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

# Create filter for one-way flight, excluding basic economy
filter = create_filter(
    flight_data=[
        FlightData(
            date="2025-07-01",
            from_airport="SFO",  # San Francisco
            to_airport="LAX",    # Los Angeles
        )
    ],
    trip="one-way",
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
    exclude_basic_economy=True,  # Exclude basic economy fares
)

# Fetch flights using JS data source to get detailed information including flight numbers
result = get_flights_from_filter(filter, data_source='js')

# Display flight results
if result is not None:
    print('Best Flights:')
    for itinerary in result.best:
        first_flight = itinerary.flights[0]

        print(f"\n{itinerary.airline_names[0]} Flight {first_flight.flight_number}")
        print(f"  Route: {itinerary.departure_airport} → {itinerary.arrival_airport}")
        print(f"  Departure: {first_flight.departure_time[0]:02d}:{first_flight.departure_time[1]:02d}")
        print(f"  Arrival: {first_flight.arrival_time[0]:02d}:{first_flight.arrival_time[1]:02d}")
        print(f"  Duration: {itinerary.travel_time} min")
        print(f"  Stops: {len(itinerary.flights) - 1}")
        print(f"  Aircraft: {first_flight.aircraft}")
        print(f"  Price: ${itinerary.itinerary_summary.price:.2f}")

        # If multi-leg flight, show all segments
        if len(itinerary.flights) > 1:
            print("  Segments:")
            for i, flight in enumerate(itinerary.flights, 1):
                print(f"    {i}. {flight.airline_name} {flight.flight_number}: "
                      f"{flight.departure_airport} → {flight.arrival_airport}")
```

**Key Points:**
- Set `exclude_basic_economy=True` to filter out basic economy fares
- Use `data_source='js'` to get detailed flight information including flight numbers
- Access individual flight details through `itinerary.flights[0]` for the first segment
- Multi-leg flights have multiple entries in `itinerary.flights`

---

## Example 2: Complete Roundtrip Booking Workflow

Search for roundtrip flights and get all return flight options with flight numbers after selecting an outbound flight. This example supports both direct and connecting flights.

```python
from fast_flights import (
    create_filter,
    get_flights_from_filter,
    create_return_flight_filter,
    get_return_flight_options,
    FlightData,
    Passengers,
)

# Step 1: Search for roundtrip flights (outbound options)
print("Step 1: Searching for outbound flights (SFO → MCO, Nov 18)")
print("-" * 80)

filter = create_filter(
    flight_data=[
        FlightData(date="2025-11-18", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-11-25", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
    max_stops=2,
)

outbound_results = get_flights_from_filter(filter, data_source='js')

if outbound_results is None or len(outbound_results.best) == 0:
    print("No outbound flights found!")
    exit(1)

print(f"✓ Found {len(outbound_results.best)} best outbound flights\n")

# Step 2: User selects an outbound flight
print("Step 2: Selecting outbound flight")
print("-" * 80)

selected_outbound = outbound_results.best[0]
first_flight = selected_outbound.flights[0]

print(f"Selected: {selected_outbound.airline_names[0]} Flight {first_flight.flight_number}")
print(f"Route: {selected_outbound.departure_airport} → {selected_outbound.arrival_airport}")
print(f"Type: {'Direct flight' if len(selected_outbound.flights) == 1 else f'Connecting ({len(selected_outbound.flights)} legs)'}")

# Show all legs for connecting flights
if len(selected_outbound.flights) > 1:
    for i, f in enumerate(selected_outbound.flights, 1):
        print(f"  Leg {i}: {f.airline} {f.flight_number} ({f.departure_airport} → {f.arrival_airport})")

print(f"Date: {first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}")
print(f"Price: ${selected_outbound.itinerary_summary.price:.2f}")
print(f"TFU: {selected_outbound.tfu}\n")

# Step 3: Generate return flight search TFS
print("Step 3: Generating return flight search")
print("-" * 80)

# Build connecting_segments list if this is a multi-leg flight
connecting_segments = None
if len(selected_outbound.flights) > 1:
    connecting_segments = []
    for i in range(1, len(selected_outbound.flights)):
        segment = selected_outbound.flights[i]
        # Use next segment's departure as this segment's arrival, or itinerary arrival for last segment
        to_airport = selected_outbound.flights[i+1].departure_airport if i+1 < len(selected_outbound.flights) else selected_outbound.arrival_airport
        connecting_segments.append({
            'from': segment.departure_airport,
            'to': to_airport,
            'airline': segment.airline,
            'flight_number': segment.flight_number,
        })

return_search_tfs = create_return_flight_filter(
    outbound_date=f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}",
    outbound_from=selected_outbound.departure_airport,
    outbound_to=selected_outbound.arrival_airport,
    outbound_airline=first_flight.airline,
    outbound_flight_number=first_flight.flight_number,
    connecting_segments=connecting_segments,  # Include connecting segments if applicable
    return_date="2025-11-25",
)

print(f"Generated return search TFS: {return_search_tfs[:50]}...\n")

# Step 4: Fetch all return flight options with flight numbers
print("Step 4: Fetching return flight options with flight numbers")
print("-" * 80)

try:
    # Use mode='fallback' for best reliability - returns flight numbers!
    return_options = get_return_flight_options(
        return_search_tfs,
        mode='fallback',
        tfu=selected_outbound.tfu  # Pass TFU from selected outbound flight
    )

    print(f"\n✓ Successfully fetched {len(return_options)} return flight options")
    print("\nReturn Flight Options:")
    print("-" * 80)

    # Display top 10 return options
    for i, option in enumerate(return_options[:10], 1):
        print(f"\n{i}. {option.airline} {option.flight_number}")
        print(f"   Route: {option.departure_airport} → {option.arrival_airport}")
        print(f"   Date: {option.departure_date}")
        print(f"   Departure: {option.departure_time}")
        print(f"   Arrival: {option.arrival_time}")
        print(f"   Duration: {option.duration_minutes} min ({option.duration_minutes // 60}h {option.duration_minutes % 60}m)")
        print(f"   Stops: {option.stops}")
        print(f"   Aircraft: {option.aircraft or 'N/A'}")
        print(f"   Total Price: ${option.total_price:.2f} {option.currency}")

    if len(return_options) > 10:
        print(f"\n... and {len(return_options) - 10} more return flight options")

except Exception as e:
    print(f"\n⚠ Error: {e}")
```

**Key Points:**
- Roundtrip searches require 2 `FlightData` entries (outbound and return dates)
- **Connecting flights are fully supported** - the library automatically encodes all flight segments
- Use `create_return_flight_filter()` to generate TFS for return flight search
- Use `get_return_flight_options()` to fetch all return flight options with flight numbers
- **`mode='fallback'` now returns flight numbers** - no additional setup required!
- **TFU parameter is preserved** - pass `tfu=selected_outbound.tfu` to maintain session continuity

---

## Example 3: Decoding TFS Strings

Decode a TFS string to see which flights are selected in a roundtrip booking.

```python
from fast_flights import decode_return_flight_tfs

# TFS string representing a roundtrip with connecting flights selected
tfs = "CBwQAhppEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTEFTKgJGOTIENDE1OCIgCgNMQVMSCjIwMjUtMTEtMTgaA01DTyoCRjkyBDE4NzYoAWoMCAISCC9tLzBkNmxwcgcIARIDTUNPGiUSCjIwMjUtMTEtMjUoAWoHCAESA01DT3IMCAISCC9tLzBkNmxwQAFIAXABggECCAGYAQE"

try:
    decoded = decode_return_flight_tfs(tfs)

    print("Decoded TFS:")
    print(f"  Query Type: {decoded['query_type']}")
    print(f"  Step: {decoded['step']}")

    print(f"\n  Outbound Flight Segments:")
    for i, segment in enumerate(decoded['outbound_segments'], 1):
        print(f"    {i}. {segment['airline']} {segment['flight_number']}: {segment['from_airport']} → {segment['to_airport']}")

    if decoded['return_segments']:
        print(f"\n  Return Flight Segments:")
        for i, segment in enumerate(decoded['return_segments'], 1):
            print(f"    {i}. {segment['airline']} {segment['flight_number']}: {segment['from_airport']} → {segment['to_airport']}")
    else:
        print(f"\n  Return Flight: Not yet selected")

    print("\n✓ TFS decoding successful!")

except Exception as e:
    print(f"\n⚠ Error decoding TFS: {e}")
```

**Output:**
```
Decoded TFS:
  Query Type: 28
  Step: 2

  Outbound Flight Segments:
    1. F9 4158: SFO → LAS
    2. F9 1876: LAS → MCO

  Return Flight: Not yet selected

✓ TFS decoding successful!
```

**Key Points:**
- `decode_return_flight_tfs()` decodes the protobuf data in TFS strings
- **Now returns `outbound_segments` and `return_segments` arrays** for multi-leg flights
- Maintains backward compatibility with single `outbound` and `return` dicts
- `step=2` indicates a return flight selection page
- Useful for debugging or extracting flight details from URLs

---

## Example 4: Direct Flight-Only Search

If you only want direct flights (no connections), filter for single-leg itineraries:

```python
from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

filter = create_filter(
    flight_data=[
        FlightData(date="2025-11-18", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-11-25", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
    max_stops=0,  # Direct flights only
)

result = get_flights_from_filter(filter, data_source='js')

# Filter for direct flights only
direct_flights = [itin for itin in result.best if len(itin.flights) == 1]

print(f"Found {len(direct_flights)} direct flights")
for itin in direct_flights[:5]:
    flight = itin.flights[0]
    print(f"{flight.airline} {flight.flight_number}: ${itin.itinerary_summary.price:.2f}")
```

**Key Points:**
- Set `max_stops=0` to prefer direct flights in search
- Filter results by `len(itin.flights) == 1` for guaranteed direct flights
- Direct flights have exactly one entry in the `flights` list

---

## Data Source Comparison

### For Initial Flight Searches (Outbound)

| Feature | `data_source='html'` | `data_source='js'` |
|---------|---------------------|----------------------|
| **Flight Numbers** | ❌ No | ✅ Yes |
| **Airline Names** | ✅ Yes | ✅ Yes |
| **Departure/Arrival Times** | ✅ Yes | ✅ Yes |
| **Duration** | ✅ Yes | ✅ Yes |
| **Price** | ✅ Yes | ✅ Yes |
| **Aircraft Type** | ❌ No | ✅ Yes |
| **Codeshare Info** | ❌ No | ✅ Yes |
| **Layover Details** | Limited | ✅ Detailed |
| **TFU Parameter** | ✅ Yes | ✅ Yes |
| **Connecting Flights** | ✅ Yes | ✅ Yes |
| **Setup Required** | None | None |

### For Return Flight Searches

| Feature | `mode='common'` | `mode='fallback'` |
|---------|----------------|-------------------|
| **Flight Numbers** | ⚠️ Sometimes | ✅ Yes |
| **All Other Details** | ✅ Yes | ✅ Yes |
| **Setup Required** | None | None |
| **Reliability** | Medium | ✅ High |
| **TFU Support** | ✅ Yes | ✅ Yes |
| **Connecting Flights** | ✅ Yes | ✅ Yes |

**Note:** `mode='fallback'` now successfully returns flight numbers for return flights without requiring Playwright installation!

---

## Fetch Modes

The `mode` parameter controls how pages are fetched:

| Mode | Description | Use Case |
|------|-------------|----------|
| `common` | Direct HTTP scraping | Fast, works for some return flights |
| `fallback` | Tries `common`, falls back to Playwright serverless | **Recommended** - best reliability, returns flight numbers |
| `force-fallback` | Always uses Playwright serverless | Requires browserless.io authentication |
| `local` | Uses local Playwright installation | Development (requires `pip install 'fast-flights[local]'`) |
| `bright-data` | Uses Bright Data proxy service | Production (requires BRIGHT_DATA_API_KEY) |

**Recommendations:**
- **For outbound flights:** Use `data_source='js'` with `mode='common'` (or `mode='fallback'` for maximum reliability)
- **For return flights:** Use `mode='fallback'` (now returns flight numbers!)
- **TFU parameter:** Always pass `tfu=selected_outbound.tfu` to return flight functions

---

## Complete Workflow Example

Here's a minimal complete roundtrip booking workflow:

```python
from fast_flights import (
    create_filter,
    get_flights_from_filter,
    create_return_flight_filter,
    get_return_flight_options,
    FlightData,
    Passengers,
)

# Step 1: Search for outbound flights
filter = create_filter(
    flight_data=[
        FlightData(date="2025-11-18", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-11-25", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
    exclude_basic_economy=True,
)

outbound = get_flights_from_filter(filter, data_source='js')

# Step 2: Select an outbound flight (direct or connecting)
selected = outbound.best[0]
first_flight = selected.flights[0]

print(f"Selected outbound: {selected.airline_names[0]} {first_flight.flight_number}")
print(f"Price: ${selected.itinerary_summary.price:.2f}")
print(f"Type: {'Direct' if len(selected.flights) == 1 else f'{len(selected.flights)}-leg connecting'}")

# Step 3: Build connecting segments if needed
connecting_segments = None
if len(selected.flights) > 1:
    connecting_segments = []
    for i in range(1, len(selected.flights)):
        segment = selected.flights[i]
        to_airport = selected.flights[i+1].departure_airport if i+1 < len(selected.flights) else selected.arrival_airport
        connecting_segments.append({
            'from': segment.departure_airport,
            'to': to_airport,
            'airline': segment.airline,
            'flight_number': segment.flight_number,
        })

# Step 4: Get return flight options
return_tfs = create_return_flight_filter(
    outbound_date=f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}",
    outbound_from=selected.departure_airport,
    outbound_to=selected.arrival_airport,
    outbound_airline=first_flight.airline,
    outbound_flight_number=first_flight.flight_number,
    connecting_segments=connecting_segments,
    return_date="2025-11-25",
)

return_options = get_return_flight_options(return_tfs, mode='fallback', tfu=selected.tfu)

# Step 5: Display return options
print(f"\n{len(return_options)} return flight options:")
for i, option in enumerate(return_options[:5], 1):
    print(f"{i}. {option.airline} {option.flight_number}: ${option.total_price:.2f}")
```

---

## Error Handling

Always handle potential errors when fetching flights:

```python
try:
    result = get_flights_from_filter(filter, data_source='js')

    if result is None:
        print("No flights found")
    else:
        print(f"Found {len(result.best)} flights")

except Exception as e:
    print(f"Error fetching flights: {e}")
```

For return flights:

```python
try:
    return_options = get_return_flight_options(
        tfs,
        mode='fallback',
        tfu=selected_outbound.tfu
    )
    print(f"Found {len(return_options)} return flights")
except Exception as e:
    print(f"Error: {e}")
```

---

## Additional Resources

- **GitHub Repository**: [fast-flights](https://github.com/you/fast-flights)
- **Full Documentation**: See README.md
- **Test Scripts**: Check the `test_*.py` files for more examples
