<div align="center">

# flights (fast-flights)

The fast, robust, strongly-typed Google Flights scraper (API) implemented in Python. Based on Baes64-encoded Protobuf string.

```haskell
$ pip install fast-flights
```

</div>

## Usage

To use `fast-flights`, you'll first create a filter (inherited from `?tfs=`) to perform a request.
Then, add `flight_data`, `trip`, `seat` and `passengers` info to use the API directly.

Honorable mention: I like birds. Yes, I like birds.

```python
from fast_flights import FlightData, Passengers, create_filter, get_flights

# Create a new filter
filter = create_filter(
    flight_data=[
        # Include more if it's not a one-way trip
        FlightData(
            date="2024-07-02",  # Date of departure
            from_airport="TPE", 
            to_airport="MYJ"
        ),
        # ... include more for round trips and multi-city trips
    ],
    trip="one-way",  # Trip (round-trip, one-way, multi-city)
    seat="economy",  # Seat (economy, premium economy, business or first)
    passengers=Passengers(
        adults=2,
        children=1,
        infants_in_seat=0,
        infants_on_lap=0
    ),
)

# Get flights with a filter
result = get_flights(filter)

# The price is currently... low/typical/high
print("The price is currently", result.current_price)

# Display the first flight
print(result.flights[0])
```

Additionally, you can use the `Airport` enum to search for airports in code (as you type)! (See `_generated_enum.py` in source)

```python
Airport.TAIPEI
              |---------------------------------|
              | TAIPEI_SONGSHAN_AIRPORT         |
              | TAPACHULA_INTERNATIONAL_AIRPORT |
              | TAMPA_INTERNATIONAL_AIRPORT     |
              | ... 5 more                      |
              |---------------------------------|
```

## How it's made

The other day, I was making a chat-interface-based trip recommendation app and wanted to add a feature that can search for flights available for booking. My personal choice is definitely [Google Flights](https://flights.google.com), since Google always has the best and organized data on the web. Therefore, I looked it up.

> 🔎 **Search** <kbd>Google</kbd><br />
> google flights api
