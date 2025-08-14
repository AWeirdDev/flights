from fflights import FlightQuery, query, get_flights

q = query(
    flights=[
        FlightQuery(
            date="2025-12-22",
            from_airport="MYJ",
            to_airport="TPE",
        )
    ],
    currency="TWD",
)
get_flights(q)
