from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple


@dataclass
class Result:
    current_price: Literal["low", "typical", "high"]
    flights: List[Flight]


@dataclass
class Connection:
    departure: str
    arrival: str
    arrival_time_ahead: str
    duration: str
    name: str
    delay: Optional[str]
    flight_number: Optional[str]
    departure_airport: Optional[str]
    arrival_airport: Optional[str]


@dataclass
class Flight:
    is_best: bool
    name: str
    departure: str
    arrival: str
    arrival_time_ahead: str
    duration: str
    stops: int
    delay: Optional[str]
    price: str
    flight_number: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    connecting_airports: Optional[List[Tuple[str, str]]] = None  # List of (airport_code, layover_duration)
    connections: Optional[List[Connection]] = None
