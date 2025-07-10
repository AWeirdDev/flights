from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple, Dict, Any


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
    aircraft: Optional[str] = None  # Aircraft type for this segment
    operated_by: Optional[str] = None  # Operator for this segment if different


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
    price: float
    flight_number: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    connecting_airports: Optional[List[Tuple[str, str]]] = None  # List of (airport_code, layover_duration)
    connections: Optional[List[Connection]] = None
    emissions: Optional[Dict[str, Any]] = None  # e.g. {"kg": 502, "percentage": -22}
    operated_by: Optional[List[str]] = None  # List of operators if different from airline
    aircraft_details: Optional[str] = None  # e.g. "Boeing 777-300ER"
