from fast_flights import create_filter, get_flights_from_filter, FlightData, Passengers

filter = create_filter(
    flight_data=[
        # Include more if it's not a one-way trip
        FlightData(
            date="2025-07-01",  # Date of departure
            from_airport="TPE",  # Departure (airport)
            to_airport="MYJ",  # Arrival (airport)
        )
    ],
    trip="one-way",  # Trip type
    passengers=Passengers(adults=2),  # Passengers
    seat="economy",  # Seat type
    max_stops=1,  # Maximum number of stops
)
print(filter.as_b64().decode("utf-8"))
print(get_flights_from_filter(filter, mode="fallback"))
