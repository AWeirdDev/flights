# :material-airplane-search: Flights
A fast, robust Google Flights scraper (API) for Python. (Probably)

`fast-flights` uses Base64-encoded [Protobuf](https://developers.google.com/protocol-buffers) strings to generate the **`tfs` query parameter**, which stores all the information for a lookup request. We then parse the HTML content and extract the info we need using `selectolax`.

```sh
pip install fast-flights
```

## Getting started
Here's `fast-flights` in 3 steps:

1. **Import** the package
2. Add the **filters**
3. **Search** for flights

How simple is that? (...and beginner-friendly, too!)

```python
from fast_flights import FlightData, Passengers, Result, get_flights

result: Result = get_flights(
    flight_data=[
        FlightData(date="2025-01-01", from_airport="TPE", to_airport="MYJ")# (1)!
    ],
    trip="one-way",# (2)!
    seat="economy",# (3)!
    passengers=Passengers(adults=2, children=1, infants_in_seat=0, infants_on_lap=0),# (4)!
    fetch_mode="fallback",#(5)!
)

print(result)
```

1. :material-airport: This specifies the (desired) date of departure for the outbound flight. Make sure to change the date!
2. :fontawesome-solid-person-walking-luggage: This specifies the trip type (`round-trip` or `one-way`). Note that `multi-city` is **not yet** supported.
3. :material-seat: Money-spending time! This specifies the seat type, which is `economy`, `premium-economy`, `business`, or `first`.
4. :fontawesome-solid-people-line: Nice interface, eh? This specifies the number of a specific passenger type.
5. :fontawesome-solid-person-falling: Sometimes, the data is built on demand on the client-side, while the core of `fast-flights` is built around scrapers from the ground up. We support fallbacks that run Playwright serverless functions to fetch for us instead. You could either specify `common` (default), `fallback` (recommended), or `force-fallback` (100% serverless Playwright). You do not need to install Playwright in order for this to work.
