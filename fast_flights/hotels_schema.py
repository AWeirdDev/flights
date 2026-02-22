from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Hotel:
    name: str
    price_per_night: int
    total_price: int
    currency: str
    stars: int
    rating: float
    reviews: str
    source: str
    amenities: List[str]


@dataclass
class HotelResult:
    hotels: List[Hotel]
