from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional, Tuple, Union

IATACode = str

# HTML parsing method will resolve to these classes
@dataclass
class HTMLParsedFlight:
    is_best: bool
    name: str
    departure: str
    arrival: str
    arrival_time_ahead: str
    duration: str
    stops: int
    delay: Optional[str]
    price: str

@dataclass
class HTMLParsedResult:
    current_price: Literal["low", "typical", "high"]
    flights: List[HTMLParsedFlight]

# see data_discovery.ipynb

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

class Trip:
    departure_airport: IATACode
    departure_airport_name: str
    departure_time: datetime
    arrival_airport: IATACode
    arrival_airport_name: str
    arrival_time: datetime
    price: int
    num_stops: int
    flights: List[Flight]

    def __init__(self, trip_data: FlightsAPIRawData):
        pass

class Flight:
    airline: IATACode
    airline_name: str
    depature_time: datetime
    departure_airport: IATACode
    arrival_time: datetime

    fare_class: str
    carry_on_bag_allowance: int
    checked_bag_allowance: int

    seat_pitch: int

    def __init__(self, flight_data: FlightsAPIRawData):
        data_root = raw_data[0]
        depart_date = data_root[4]
        depart_hour = data_root[5][0] or 0
        depart_minute = data_root[5][1] if len(data_root[5]) == 2 else 0
        self.depature_time = datetime(*depart_date, hour=depart_hour, minute=depart_minute)
        arrive_date = data_root[7]
        arrive_hour = data_root[8][0] or 0
        arrive_minute = data_root[8][1] if len(data_root[8]) == 2 else 0
        self.arrival_time = datetime(*arrive_date, hour=arrive_hour, minute=arrive_minute)
        self.price = data_root[9]
        self.num_stops = len(data_root[13]) if data_root[13] else 0
        self.airline = data_root[0]
        self.flight_nums = [leg[22][1] for leg in data_root[2]]

    def __str__(self) -> str:
        return f'{self.airline}{",".join(self.flight_nums)}: ${self.price}, {self.num_stops} stops, {self.depature_time} -> {self.arrival_time}'


class FlightsAPIResult:
    best: List[Trip]
    other: List[Trip]
    other_remaining: int

    raw_data: FlightsAPIRawData

    def __init__(self, best: List[Trip], other: List[Trip], other_remaining: int, raw_data: FlightsAPIRawData):
        self.best = best
        self.other = other
        self.other_remaining = other_remaining
        self.raw_data = raw_data

    @classmethod
    def parse(cls, data_root: List[FlightsAPIRawData.RawDataValueType]) -> 'FlightsAPIResult':
        raw_data = FlightsAPIRawData(data_root)

        # TODO: fix type hints?? not sure if even possible
        best = [Trip(flight_data) for flight_data in raw_data[2,0]]
        other = [Trip(flight_data) for flight_data in raw_data[3,0]]
        return cls(best, other, raw_data[3,1], raw_data)
