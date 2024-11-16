from typing import List, Literal, Union, overload

from .filter_builder import Flight, Passengers
from .primp import Client
from .airflights import Tfs, make_tfs, generate_trail

default_passengers = Passengers()


@overload
def get(
    *,
    flights: List[Flight],
    passengers: Passengers = default_passengers,
    trip: Literal["one_way", "round_trip", "multi_city"] = "one_way",
    seat: Literal["economy", "premium_economy", "business", "first"] = "economy",
    verbose: Literal[True] = True,
    **client_kwargs,
) -> tuple[Tfs, str]: ...


@overload
def get(
    *,
    flights: List[Flight],
    passengers: Passengers = default_passengers,
    trip: Literal["one_way", "round_trip", "multi_city"] = "one_way",
    seat: Literal["economy", "premium_economy", "business", "first"] = "economy",
    verbose: Literal[False] = False,
    **client_kwargs,
) -> str: ...


def get(
    *,
    flights: List[Flight],
    passengers: Passengers = default_passengers,
    trip: Literal["one_way", "round_trip", "multi_city"] = "one_way",
    seat: Literal["economy", "premium_economy", "business", "first"] = "economy",
    verbose: Literal[True, False] = False,
    **client_kwargs,
) -> Union[tuple[Tfs, str], str]:
    client = Client(
        **(
            {"verify": False, "follow_redirects": True, "impersonate": "chrome_128"}
            | client_kwargs
        )
    )  # type: ignore

    tfs = make_tfs(
        flights_data=[flight.dict() for flight in flights],
        seat_data=seat,
        passengers_data=passengers.list(),
        trip_data=trip,
    )
    print(tfs.base64())
    res = client.get(
        "https://www.google.com/travel/flights/search",
        params={"tfs": tfs.base64() + "_" * 12 + generate_trail()},
    )

    assert res.status_code == 200, f"Status not OK, html:\n{res.text_markdown}"

    if verbose:
        return (tfs, res.text_markdown)

    return res.text_markdown
