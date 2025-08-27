from fast_flights import FlightQuery, Passengers, create_query, get_flights
from pprint import pprint

query = create_query(
    flights=[
        FlightQuery(
            date="2025-12-22",
            from_airport="MYJ",
            to_airport="TPE",
        ),
    ],
    seat="economy",
    trip="one-way",
    passengers=Passengers(adults=1),
    language="zh-TW",
)
res = get_flights(query)
pprint(res)
