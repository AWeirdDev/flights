from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter

# Create a new filter
filter = create_filter(
    flight_data=[
        # Include more if it's not a one-way trip
        FlightData(
            date="2025-10-04",  # Date of departure
            from_airport="SJC",
            to_airport="LAS"
        ),
        # ... include more for round trips
    ],
    trip="one-way",  # Trip (round-trip, one-way)
    seat="economy",  # Seat (economy, premium-economy, business or first)
    passengers=Passengers(
        adults=1,
        children=1,
        infants_in_seat=0,
        infants_on_lap=0
    ),
)

# Get flights with a filter
result = get_flights_from_filter(filter, data_source='js')

if result is not None:
    print('Best:')
    for flight in result.best:
        print(flight)
        print()
    print('Others:')
    for flight in result.other:
        print(flight)
        print()
