from typing import Literal, List, Optional
from .flights_impl import FlightData, Passengers, TFSData

def create_filter(
    *,
    flight_data: List[FlightData],
    trip: Literal["round-trip", "one-way", "multi-city"],
    passengers: Passengers,
    seat: Literal["economy", "premium-economy", "business", "first"],
    max_stops: Optional[int] = None,
) -> TFSData:
    """Create a filter. (``?tfs=``)

    Args:
        flight_data (list[FlightData]): Flight data as a list.
        trip ("one-way" | "round-trip" | "multi-city"): Trip type.
        passengers (Passengers): Passengers.
        seat ("economy" | "premium-economy" | "business" | "first"): Seat.
        max_stops (int, optional): Maximum number of stops. Defaults to None.
    """
    for fd in flight_data:
        fd.max_stops = max_stops

    return TFSData.from_interface(
        flight_data=flight_data, trip=trip, passengers=passengers, seat=seat
    )
