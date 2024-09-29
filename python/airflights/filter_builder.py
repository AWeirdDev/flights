from dataclasses import dataclass


@dataclass(kw_only=True)
class Flight:
    """Creates a flight filter.

    Example:

    .. code-block:: python

        flight = Flight(
            date="2024-10-01",
            from_airport="TPE",
            to_airport="MYJ"
        )

    Args:
        date (str): Date of departure for outbound flight.
        from_airport (str): Departure (airport code). Where from?
        to_airport (str): Arrival (airport code). Where to?
    """

    date: str
    from_airport: str
    to_airport: str

    def dict(self) -> dict:
        return {"date": self.date, "from": self.from_airport, "to": self.to_airport}


class Passengers:
    """Creates a passengers list.

    Note that passengers are limited to 9 or lower and there should be at least one adult per infant on lap (if any).

    .. code-block:: python

        passenger = Passengers(
            adults=1,
            children=0,
            infants_in_seat=0,
            infants_on_lap=0
        )

    Args:
        adults (int, optional): Number of adult passengers.
        children (int, optional): Number of child passengers.
        infants_in_seat (int, optional): Number of infant in seat passengers.
        infants_on_lap (int, optional): Number of infant on lap passengers.
    """

    def __init__(
        self,
        *,
        adults: int = 0,
        children: int = 0,
        infants_in_seat: int = 0,
        infants_on_lap: int = 0,
    ):
        assert (
            sum((adults, children, infants_in_seat, infants_on_lap)) <= 9
        ), "Too many passengers (> 9)"
        assert (
            infants_on_lap <= adults
        ), "You must have at least one adult per infant on lap"
        self.adults = adults
        self.children = children
        self.infants_in_seat = infants_in_seat
        self.infants_on_lap = infants_on_lap

    def list(self) -> list[str]:
        return [
            *("adult" for _ in range(self.adults)),
            *("child" for _ in range(self.children)),
            *("infant_in_seat" for _ in range(self.infants_in_seat)),
            *("infant_on_lap" for _ in range(self.infants_on_lap)),
        ]

    def __repr__(self) -> str:
        return f"Passengers({self.adults=}, {self.children=}, {self.infants_in_seat=}, {self.infants_on_lap=})"
