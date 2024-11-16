from python.airflights import Flight, Passengers, get
from fast_flights import create_filter, FlightData, Passengers as P


filter = create_filter(
    flight_data=[
        # Include more if it's not a one-way trip
        FlightData(
            date="2024-07-02",  # Date of departure
            from_airport="TPE",
            to_airport="MYJ",
        ),
        # ... include more for round trips
    ],
    trip="one-way",  # Trip (round-trip, one-way)
    seat="economy",  # Seat (economy, premium-economy, business or first)
    passengers=P(adults=2, children=1, infants_in_seat=0, infants_on_lap=0),
)
print(filter.as_b64())

print(
    get(
        flights=[Flight(date="2024-10-01", from_airport="TPE", to_airport="MYJ")],
        passengers=Passengers(adults=3),
        trip="one_way",
        seat="economy",
        verbose=True,
    )[0]
)
