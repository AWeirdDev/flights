# Airports

To search for an airport, you could use the `search_airports()` API:

```python
airport = search_airports("taipei")[0]
airport
# Airport.TAIPEI_SONGSHAN_AIRPORT
```

If you're unfamiliar with those 3-letter airport codes (such as "MYJ" for Matsuyama, "TPE" for Taipei, "LAX" for Los Angeles, etc.), you could pass in an `Airport` enum to a `FlightData` object:

```python
taipei = search_airports("taipei")[0]
los = search_airports("los angeles")[0]

filter = create_filter(
    flight_data=[
        FlightData(
            date="2025-01-01",
            from_airport=taipei,
            to_airport=los
        )
    ],
    ...
)
```

I love airports. Navigating them was like an adventure when I was a kid. I really thought that airports have everything in them, I even drew an entire airport containing (almost) a city at this point... naively.
