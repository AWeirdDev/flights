# :material-filter: Filters
Filters are used to generate the `tfs` query parameter. In short, you make queries with filters.

With the new API, there's no need to use the `create_filter()` function, as you can use `get_flights()` and add the filter parameters directly.

```python
get_flights(..., fetch_mode="fallback")

# is equivalent to:

filter = create_filter(...)
get_flights_from_filter(filter, mode="fallback")
```

## FlightData
This specifies the general flight data: the date, departure & arrival airport, and the maximum number of stops (untested).

```python
data = FlightData(
    date="2025-01-01", 
    from_airport="TPE", 
    to_airport="MYJ", 
    airlines=["DL", "AA", "STAR_ALLIANCE"], # optional
    max_stops=10  # optional
)
```

Note that for `round-trip` trips, you'll need to specify more than one `FlightData` object for the `flight_data` parameter.

The values in `airlines` has to be a valid 2 letter IATA airline code, case insensitive. They can also be one of `SKYTEAM`, `STAR_ALLIANCE` or `ONEWORLD`. Note that the server side currently ignores the `airlines` parameter added to the `FlightData`s of all the flights which is not the first flight. In other words, if you have two `FlightData`s for a `round-trip` trip: JFK-MIA and MIA-JFK, and you add `airlines` parameter to both `FlightData`s, only the first `airlines` will be considered for the whole search. So technically `airlines` could be a better fit as a parameter for `TFSData` but adding to `FlightData` is the correct usage because if the backend changes and brings more flexibility to filter with different airlines for different flight segments in the future, which it should, this will come in handy.

## Trip
Either one of:

- `round-trip`
- `one-way`
- :material-alert: `multi-city` (unimplemented)

...can be used.

If you're using `round-trip`, see [FlightData](#flightdata).

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

CLI & programmatic examples

- From the bundled example CLI (`example.py`) you can supply the number of children with the `--children` flag:

```bash
python example.py --origin LHR --destination SLC --depart_date 2026-05-23 --return_date 2026-05-30 --adults 2 --children 1
```

- Programmatically, pass the children count into `Passengers` when creating a filter or calling `get_flights`:

```python
from fast_flights import Passengers, create_filter, get_flights

passengers = Passengers(adults=2, children=1)
# use create_filter(...) or pass passengers to get_flights(...)
```

## Example
Here's a simple example on how to create a filter:

```python
filter: TFSData = create_filter(
    flight_data=[
        FlightData(
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

filter.as_b64()  # Base64-encoded (bytes)
filter.to_string()  # Serialize to string
```

## Passing cookies (binary parameter)

Both `get_flights_from_filter(...)` and `get_flights(...)` accept a new optional parameter `cookies: bytes | None` which allows you to embed cookies as a binary payload that will be forwarded to the underlying fetchers.

Supported cookie formats (the function will try them in this order):

- JSON bytes: UTF-8 JSON encoding of a dict (e.g. `{ "CONSENT": "...", "SOCS": "..." }`). This will be set as `request_kwargs['cookies']`.
- Pickle bytes: a pickled `dict` of cookie-name -> value; this will be set as `request_kwargs['cookies']`.
- Raw Cookie header: if the bytes can't be parsed as JSON or pickle, they are decoded as UTF-8 and set as the `Cookie` HTTP header (`request_kwargs['headers']['Cookie']`).

Examples:

- JSON-encoded cookies as bytes (recommended):

```python
import json
cookies = {"CONSENT": "PENDING+987", "SOCS": "CAESH..."}
cookies_bytes = json.dumps(cookies).encode("utf-8")
result = get_flights_from_filter(filter, cookies=cookies_bytes)
```

- Raw header example (when you already have a Cookie header string):

```python
cookies_bytes = b"CONSENT=PENDING+987; SOCS=CAESH..."
result = get_flights_from_filter(filter, cookies=cookies_bytes)
```

Backward compatibility:

- You can still pass cookies the old way via `request_kwargs={'cookies': {'CONSENT': '...', 'SOCS': '...'}}` — this is honored when `cookies` (binary) is not provided.
- If both `cookies` (binary) and `request_kwargs` are provided, the parsed binary `cookies` take precedence and will override any `cookies` or `Cookie` header in `request_kwargs`.

Security and privacy note:

- Cookies may contain sensitive values. Avoid logging or committing cookies into source control and only supply cookies you trust.

### Configurable default consent cookies

The library embeds a small default consent cookie bundle used to bypass common Google consent gating. If you prefer to disable or explicitly control this behavior, both `get_flights_from_filter` and `get_flights` accept a boolean flag `cookie_consent: bool` (default `True`).

- To use the embedded default cookies (the default behavior):

```python
# will apply embedded default cookies unless you provide cookies/request_kwargs explicitly
result = get_flights_from_filter(filter, cookie_consent=True)
```

- To disable automatic application of the embedded default cookies:

```python
# will NOT add any embedded cookies; you can still pass cookies explicitly via request_kwargs or the binary `cookies` parameter
result = get_flights_from_filter(filter, cookie_consent=False)
```

You can also pass the flag through `get_flights`:

```python
result = get_flights(..., cookie_consent=False)
```
