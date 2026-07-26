---
title: "Queries"
---

Queries are used to generate the `?tfs` query parameter.

```python
from fast_flights import (
    FlightQuery,
    Passengers,
    create_query
)

query = create_query(
    flights=[
        FlightQuery(
            date="2067-06-07",
            from_airport="MYJ",
            to_airport="TPE"
        ),
    ],
    seat="economy",
    trip="one-way",
    passengers=Passengers(adults=1, infants_in_seat=2),
    language="en"
)

# ...then you get get flights with the query!
# res = get_flights(query)
```

Alternatively, you can use natural text to get flights instead of using `create_query()`:

```python
get_flights(
    "Flights from TPE to MYJ on 2067-06-07 one way economy class"
)
```


## FlightQuery
This specifies the flight leg and its per-leg filters:

```python
data = FlightQuery(
    date="2025-01-01", 
    from_airport="TPE", 
    to_airport="MYJ", 
    airlines=["DL", "AA", "STAR_ALLIANCE"], # optional
    max_stops=1,                         # optional
    earliest_departure_hour=7,           # 7:00 AM
    latest_departure_hour=18,            # keeps departures through 18:59
    earliest_arrival_hour=10,
    latest_arrival_hour=23,
    max_duration_minutes=720,
    connecting_airports=["HND", "NRT"],
    min_layover_minutes=60,
    max_layover_minutes=240,
    less_emissions_only=True,
)
```

Note that for `round-trip` trips, you'll need to specify more than one `FlightQuery` object for the `flight_data` parameter.

The values in `airlines` has to be a valid 2 letter IATA airline code, case insensitive. They can also be one of `SKYTEAM`, `STAR_ALLIANCE` or `ONEWORLD`. Note that the server side currently ignores the `airlines` parameter added to the `FlightQuery`s of all the flights which is not the first flight. In other words, if you have two `FlightQuery`s for a `round-trip` trip: JFK-MIA and MIA-JFK, and you add `airlines` parameter to both `FlightQuery`s, only the first `airlines` will be considered for the whole search. So technically `airlines` could be a better fit as a parameter for `TFSData` but adding to `FlightQuery` is the correct usage because if the backend changes and brings more flexibility to filter with different airlines for different flight segments in the future, which it should, this will come in handy.

`create_query()` also supports filters that apply to the whole search:

```python
query = create_query(
    flights=[data],
    currency="USD",
    max_price=1500,
    carry_on_bags=1,
    checked_bags=1,
    hide_separate_and_self_transfer=True,
    exclude_basic_economy=True,
)
```

`max_price` uses the currency selected by `currency`. Baggage counts ask Google
to include its estimated bag fees in displayed prices.

## Trip
Either one of:

- `round-trip`
- `one-way`
- :material-alert: `multi-city` (unimplemented)

...can be used.

If you're using `round-trip`, see [FlightQuery](#FlightQuery).

## Seat
Now it's time to see who's the people who got $$$ dollar signs in their names. Either one of:

- `economy`
- `premium-economy`
- `business`
- `first`

...can be used, sorted from the least to the most expensive.

## Passengers
A family trip? No problem. Just tell us how many adults, children & infants are there.

There are some checks made, though:

- The sum of `adults`, `children`, `infants_in_seat` and `infants_on_lap` must not exceed `9`.
- You must have at least one adult per infant on lap (which frankly, is easy to forget).

```python
passengers = Passengers(
    adults=2,
    children=1,
    infants_in_seat=0,
    infants_on_lap=0
)
```

## Example
Here's a simple example on how to create a filter:

```python
query: Query = create_query(
    flight_data=[
        FlightQuery(
            date="2025-01-01",
            from_airport="TPE",
            to_airport="MYJ",
        )
    ],
    trip="round-trip",
    passengers=Passengers(adults=2, children=1, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
    max_stops=1,
)

query.to_bytes()  # Base64-encoded (bytes)
query.to_str()  # Serialize to string
```
