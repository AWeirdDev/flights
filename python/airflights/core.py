from typing import List, Literal

from .filter_builder import Flight, Passengers
from .primp import Client
from .airflights import make_tfs, generate_trail

default_passengers = Passengers()


def get(
    *,
    flights: List[Flight],
    passengers: Passengers = default_passengers,
    trip: Literal["one_way", "round_trip", "multi_city"] = "one_way",
    seat: Literal["economy", "premium_economy", "business", "first"] = "economy",
    **client_kwargs,
):
    client = Client(
        **(
            {"verify": False, "follow_redirects": True, "impersonate": "chrome_128"}
            | client_kwargs
        )
    )  # type: ignore
    res = client.get(
        "https://www.google.com/travel/flights/search",
        params={
            "tfs": (
                make_tfs(
                    flights_data=[flight.dict() for flight in flights],
                    seat_data=seat,
                    passengers_data=passengers.list(),
                    trip_data=trip,
                ).base64()
                + "_" * 12
                + generate_trail()
            )
        },
    )
    assert res.status_code == 200, f"Status not OK, html:\n{res.text_markdown}"
    return res.text_markdown
