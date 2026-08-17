# pyright: reportAny=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import json

from selectolax.lexbor import LexborHTMLParser

from .exceptions import FlightsNotFound
from .model import (
    Airline,
    Airport,
    Alliance,
    CarbonEmission,
    Flights,
    JsMetadata,
    SimpleDatetime,
    SingleFlight,
)


class ResultList(list[Flights]):
    """Searched flights list, with metadata attached."""

    metadata: JsMetadata


def parse(html: str) -> ResultList:
    parser = LexborHTMLParser(html)

    # find js
    script = parser.css_first(r"script.ds\:1")
    return parse_js(script.text())


def _parse_time(value: list[int | None] | None) -> tuple[int, int]:
    """Expand a JS time pair that omits default (zero) components.

    Google drops trailing zero components and uses ``None`` for a leading
    zero, so ``[8]`` means 08:00 and ``[None, 31]`` means 00:31.
    """
    # A missing element and an explicit None both mean "omitted component",
    # and an omitted component is always zero.
    padded = [*(value or []), None, None]
    return (padded[0] or 0, padded[1] or 0)


# Data discovery by @kftang, huge shout out!
def parse_js(js: str):
    data = js.split("data:", 1)[1].rsplit(",", 1)[0]

    if data.endswith("errorHasStatus: true"):
        raise FlightsNotFound("no flights found; received error")

    payload = json.loads(data)

    alliances = []
    airlines = []

    (alliances_data, airlines_data) = (
        payload[7][1][0],
        payload[7][1][1],
    )

    for code, name in alliances_data:
        alliances.append(Alliance(code=code, name=name))

    for code, name in airlines_data:
        airlines.append(Airline(code=code, name=name))

    meta = JsMetadata(alliances=alliances, airlines=airlines)

    flights = ResultList()
    if payload[3][0] is None:
        return flights

    for k in payload[3][0]:
        flight = k[0]
        price = k[1][0][1]

        typ = flight[0]
        airlines = flight[1]

        sg_flights = []

        # multiple flights!
        for single_flight in flight[2]:
            from_airport = Airport(code=single_flight[3], name=single_flight[4])
            to_airport = Airport(code=single_flight[6], name=single_flight[5])
            departure_time = _parse_time(single_flight[8])
            departure_date = tuple(single_flight[20])
            departure = SimpleDatetime(date=departure_date, time=departure_time)

            arrival_time = _parse_time(single_flight[10])
            arrival_date = tuple(single_flight[21])
            arrival = SimpleDatetime(date=arrival_date, time=arrival_time)

            plane_type = single_flight[17]

            duration = single_flight[11]

            sg_flights.append(
                SingleFlight(
                    from_airport=from_airport,
                    to_airport=to_airport,
                    departure=departure,
                    arrival=arrival,
                    duration=duration,
                    plane_type=plane_type,
                )
            )

        # some additional data
        extras = flight[22]
        carbon_emission = extras[7]
        typical_carbon_emission = extras[8]

        flights.append(
            Flights(
                type=typ,
                price=price,
                airlines=airlines,
                flights=sg_flights,
                carbon=CarbonEmission(
                    typical_on_route=typical_carbon_emission, emission=carbon_emission
                ),
            )
        )

    flights.metadata = meta
    return flights
