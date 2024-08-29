# functions for evaluating which flights are best

# first determine if there are direct flights


# functionality to add later:
# compare price of direct flights to connecting ones

from typing import List, Tuple
from fast_flights import Flight


def find_shortest_flight(flights: List[Flight]) -> Flight:
    """
    Finds the flight with the shortest trip time in the provided list of flights.

    Args:
       flights (List[Flight]): List of Flight objects.

    Returns:
       Flight: The Flight object with the shortest trip time.
    """
    # Combine logic for duration conversion and finding minimum in one step
    shortest_flight = min(flights, key=lambda flight:
    int(flight.duration.split()[0] if 'hr' in flight.duration else 0) * 60 +
    int(flight.duration.split()[2] if 'min' in flight.duration else 0))

    return shortest_flight.duration



def check_direct_flights(flights: List[Flight]) -> Tuple[bool, List[Flight]]:
    """
    Check if there are any direct flights in the provided list of flights.

    Args:
        flights (List[Flight]): List of Flight objects.

    Returns:
        Tuple[bool, List[Flight]]: A tuple containing a boolean indicating if there are direct flights
                                   and a list of direct Flight objects.
    """
    direct_flights = [flight for flight in flights if flight.stops == 0]
    return (len(direct_flights) > 0, direct_flights)
