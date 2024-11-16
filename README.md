# airflights

`airflights` is a Python package to scrape Google Flights. For the Python version, visit the `legacy` directory.

```python
from airflights import Flight, get

get(
    flights=[
        Flight(
            date="2024-xx-xx",  # date of departure for outbound flight
            from_airport="TPE",
            to_airport="MYJ"
        ),
        ...
    ],
    trip="one_way",
    seat="economy",
    passengers=Passengers(
        adults=2,
        children=1,
        infants_in_seat=0,
        infants_on_lap=0
    )
)
```

## Progress of `v2`
Weird. I created Protobufs and tried to encode data with it, but it just wouldn't work. Same file, different results for different runtimes (Python OK, Rust failed)... like WTF?

I'm guessing it's because of the Base64 crate I'm using. It's currently a "simpler version" of base64 (they claimed?) but I suspect it's their fault.

Will change the deps later.
