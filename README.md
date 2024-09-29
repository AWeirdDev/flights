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
