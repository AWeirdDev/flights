from python.airflights import Flight, Passengers, get

print(
    get(
        flights=[Flight(date="2024-10-01", from_airport="TPE", to_airport="MYJ")],
        passengers=Passengers(adults=1),
        trip="one_way",
        seat="economy"
    )
)
