from fast_flights import FlightData, Passengers, create_filter, get_flights, Airport
import configparser
# My functions
from flight_times import check_direct_flights, find_shortest_flight
from check_airports import find_nearby_airports

config = configparser.ConfigParser()  # Create a ConfigParser object
config.read('josephs_preferences.ini')  # Read the configuration file for the user (me)

# Start by pulling preferences from user's config file (in this case me)
home_airport = config['basic info']['home_airport']
destination = "LAX"

# Create a new filter
filter = create_filter(
    flight_data=[
        # Include more if it's not a one-way trip
        FlightData(
            date="2024-09-02",  # Date of departure
            from_airport=home_airport,
            to_airport=destination
        ),
        # ... include more for round trips and multi-city trips
    ],
    trip="one-way",  # Trip (round-trip, one-way, multi-city)
    seat="economy",  # Seat (economy, premium-economy, business or first)
    passengers=Passengers(
        adults=2,
        children=1,
        infants_in_seat=0,
        infants_on_lap=0
    ),
)

# Get flights with a filter
result = get_flights(filter)

# The price is currently... low/typical/high
print("The price is currently", result.current_price)

# Display the first flight
print(result.flights[3])

# Check for direct flights
has_direct_flights, direct_flights = check_direct_flights(result.flights)

# Output the result
if has_direct_flights:
    print("\n\nThere are direct flights available:")
    for flight in direct_flights:
        print(flight)
else:
    print("No direct flights available.")

# Finds shortest flight
shortest_flight = find_shortest_flight(result.flights)

print('\nShortest flight duration:')
print(shortest_flight)

nearby_airports = find_nearby_airports(destination)  # or 'New York'
print(nearby_airports)
