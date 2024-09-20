from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from typing import List


class Flight():
    depart: datetime
    arrive: datetime
    price: int
    num_stops: int
    airline: str
    flight_nums: List[int]

    def __init__(self, raw_data: List):
        data_root = raw_data[0]
        depart_date = data_root[4]
        depart_hour = data_root[5][0] or 0
        depart_minute = data_root[5][1] if len(data_root[5]) == 2 else 0
        self.depart = datetime(*depart_date, hour=depart_hour, minute=depart_minute)
        arrive_date = data_root[7]
        arrive_hour = data_root[8][0] or 0
        arrive_minute = data_root[8][1] if len(data_root[8]) == 2 else 0
        self.arrive = datetime(*arrive_date, hour=arrive_hour, minute=arrive_minute)
        self.price = data_root[9]
        self.num_stops = len(data_root[13]) if data_root[13] else 0
        self.airline = data_root[0]
        self.flight_nums = [leg[22][1] for leg in data_root[2]]

    def __str__(self) -> str:
        return f'{self.airline}{",".join(self.flight_nums)}: ${self.price}, {self.num_stops} stops, {self.depart} -> {self.arrive}'

class FlightResults():
    best: List[Flight]
    other: List[Flight]
    other_remaining: int

    def __init__(self, best: List[Flight], other: list[Flight], other_remaining: int):
        self.best = best
        self.other = other
        self.other_remaining = other_remaining

    @classmethod
    def parse(cls, raw_data: List) -> 'FlightResults':
        best = [Flight(flight_data) for flight_data in raw_data[2][0]]
        other = [Flight(flight_data) for flight_data in raw_data[3][0]]
        return cls(best, other, raw_data[3][1])
