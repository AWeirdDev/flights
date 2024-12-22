from dataclasses import dataclass
from typing import Any


@dataclass
class Passengers:
    adults: int = 1
    children: int = 0
    infants_in_seat: int = 0
    infants_on_lap: int = 0

    def __post_init__(self):
        assert (
            sum((self.adults, self.children, self.infants_in_seat, self.infants_on_lap))
            <= 9
        ), "Too many passengers (> 9)"
        assert (
            self.infants_on_lap <= self.adults
        ), "You must have at least one adult per infant on lap"

    def attach(self, info: Any) -> None:
        """Attach passenger information to the protobuf message"""
        # Passenger enum values
        ADULT = 0
        CHILD = 1
        INFANT_IN_SEAT = 2
        INFANT_ON_LAP = 3

        # Add passengers in order
        for _ in range(self.adults):
            info.passengers.append(ADULT)
        for _ in range(self.children):
            info.passengers.append(CHILD)
        for _ in range(self.infants_in_seat):
            info.passengers.append(INFANT_IN_SEAT)
        for _ in range(self.infants_on_lap):
            info.passengers.append(INFANT_ON_LAP)
