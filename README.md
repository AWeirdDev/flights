<div align="center">

# flights

The fast, robust, strongly-typed Google Flights scraper (API) implemented in Python. Based on Baes64-encoded Protobuf string.

```haskell
$ pip install flights
```

</div>

## Usage

To use `flights`, you'll first create a filter (inherited from `?tfs=`) to perform a request.
Then, add `flight_data`, `trip`, `seat` and `passengers` info to use the API directly.

Honorable mention: I like birds. Yes, I like birds.

```python
from flights import FlightData, Passengers, create_filter, get_flights

# Create a new filter
filter = create_filter(
    flight_data=[
        # Include more if it's not a one-way trip
        FlightData(
            date="2024-07-02", 
            from_airport="TPE", 
            to_airport="MYJ"
        )
    ],
    trip="one-way",
    seat="economy",
    passengers=Passengers(
        adults=2,
        children=1
    ),
)

# Get flights from a filter
result = get_flights(filter)

# The price is currently... low/typical/high
print("The price is currently", result.current_price)

# Display the first flight
print(result.flights[0])
```

Additionally, you can use the `Airport` enum to search for airports in code (as you type)!

```python
Airport.TAIPEI
              |---------------------------------|
              | TAIPEI_SONGSHAN_AIRPORT         |
              | TAPACHULA_INTERNATIONAL_AIRPORT |
              | TAMPA_INTERNATIONAL_AIRPORT     |
              | ... 5 more                      |
              |---------------------------------|
```
