from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from typing import List, Literal, Optional, Dict, Union, Tuple, Iterable
from typing_extensions import TypeAlias


AirlineCode: TypeAlias = str
AirportCode: TypeAlias = str

@dataclass
class Result:
    current_price: Literal["low", "typical", "high"]
    trips: List[Trip]


@dataclass
class Trip:
    is_best: bool
    name: str
    departure: str
    arrival: str
    arrival_time_ahead: str
    duration: str
    stops: int
    delay: Optional[str]
    price: str

# JS data parsing method will resolve to these classes
class FlightsAPIRawData:
    # typedefs for the js data structures
    RawDataDecoderDictValueType = Union['RawDataDecoderDict', str]
    RawDataDecoderDict = Dict[Union[int, str], RawDataDecoderDictValueType]
    RawDataValueType = Union[List['RawDataValueType'], str, int, None, float]

    # used for implementing __getitem__ with a str key
    # TODO: Figure out best format for this
    decoder_dict: Optional[RawDataDecoderDict]
    raw_data: List[RawDataValueType]

    def __init__(self, raw_data: List[RawDataValueType], decoder_dict: Optional[RawDataDecoderDict] = None):
        self.decoder_dict = decoder_dict
        self.raw_data = raw_data

    def __getitem__(self, key: Union[int, str, Tuple[int, ...]]) -> RawDataValueType:
        if isinstance(key, int):
            return self.raw_data[key]
        elif isinstance(key, str):
            raise NotImplementedError('feature not supported yet')
            if self.decoder_dict is None:
                raise RuntimeError('decoder dict is not provided')
        elif isinstance(key, tuple):
            # make sure all elements of the tuple are int
            if not all([isinstance(el, int) for el in key]):
                raise IndexError('key provided as tuple must only have ints')

            # iterate over the raw data using the provided keys
            # we make no guarantees that the index exists
            it = self.raw_data
            for idx in key:
                it = it[idx]  # type: ignore
            return it
        else:
            raise NotImplementedError('supported key types are int, str, and tuple[int, ...]')

    def __iter__(self) -> Iterable[RawDataValueType]:
        return self.raw_data.__iter__()

def get_datetime(date_list: List[int], time_list: List[int]) -> datetime:
    year = date_list[0]
    month = date_list[1]
    day = date_list[2]

    if len(time_list) == 2:
        hour = time_list[0] or 0
        minute = time_list[1] or 0
    else:
        hour = time_list[0] or 0
        minute = 0


    return datetime(year=year, month=month, day=day, hour=hour, minute=minute)

class JTrip:
    airline: AirlineCode
    airline_name: str

    departure_airport: AirportCode
    departure_time: datetime
    arrival_airport: AirportCode
    arrival_time: datetime
    price: int
    num_stops: int
    flights: List[AdvancedFlight]

    # TODO: Add type for this
    layovers: List

    def __init__(self, trip_data: FlightsAPIRawData):
        self.airline = trip_data[0]
        self.airline_name = trip_data[1][0]
        self.flights = [AdvancedFlight(flight_data) for flight_data in trip_data[2]]
        self.departure_airport = trip_data[3]
        self.departure_time = get_datetime(trip_data[4], trip_data[5])
        self.arrival_airport = trip_data[6]
        self.arrival_time = get_datetime(trip_data[7], trip_data[8])
        self.price = trip_data[9]
        self.layovers = trip_data[13]

    def __str__(self) -> str:
        return f'{self.airline_name} flight (${self.price}) with {len(self.flights) - 1} stops from {self.departure_airport} at {self.departure_time} to {self.arrival_airport} at {self.arrival_time}'


class AdvancedFlight:
    airline: AirlineCode
    airline_name: str
    flight_number: int

    depature_time: datetime
    departure_airport: AirportCode
    arrival_time: datetime
    arrival_airport: AirportCode

    fare_class: str
    carry_on_bag_allowance: int
    checked_bag_allowance: int

    seat_pitch: int

    def __init__(self, flight_data: FlightsAPIRawData):
        self.airline = flight_data[22][0]
        self.airline_name = flight_data[22][3]
        self.flight_number = flight_data[22][1]


    def __str__(self) -> str:
        return f'{self.airline}{self.flight_number}: {self.depature_time} -> {self.arrival_time}'


class FlightsAPIResult:
    best: List[JTrip]
    other: List[JTrip]
    other_remaining: int

    raw_data: FlightsAPIRawData

    def __init__(self, best: List[JTrip], other: List[JTrip], other_remaining: int, raw_data: FlightsAPIRawData):
        self.best = best
        self.other = other
        self.other_remaining = other_remaining
        self.raw_data = raw_data

    def __str__(self) -> str:
        ret = 'Best Flights:\n'
        for trip in self.best:
            ret += f'{trip}\n'
        ret += 'Other Flights:\n'
        for trip in self.other:
            ret += f'{trip}\n'
        return ret


    @classmethod
    def parse(cls, data: List) -> 'FlightsAPIResult':
        raw_data = FlightsAPIRawData(data)
        best_trips = [JTrip(trip_data[0]) for trip_data in raw_data[2][0]] if raw_data[2] else []
        other_trips = [JTrip(trip_data[0]) for trip_data in raw_data[3][0]] if raw_data[3] else []

        return cls(best_trips, other_trips, raw_data[3][1] if raw_data[3][1] else 0, raw_data)
