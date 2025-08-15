import rjsonc
from selectolax.lexbor import LexborHTMLParser

from .model import (
    Airline,
    Airport,
    Alliance,
    JsCarbonEmission,
    JsFlights,
    JsSingleFlight,
    JsMetadata,
    SimpleDatetime,
)


class MetaList(list):
    metadata: JsMetadata


def parse(html: str) -> MetaList:
    parser = LexborHTMLParser(html)

    # find js
    script = parser.css_first(r"script.ds\:1")
    return parse_js(script.text())


# Data discovery by @kftang, huge shout out!
def parse_js(js: str):
    json = js.split("data:", 1)[1].rsplit(",", 1)[0]
    data = rjsonc.loads(json)

    alliances = []
    airlines = []

    (alliances_data, airlines_data) = (
        data[7][1][0],
        data[7][1][1],
    )

    for code, name in alliances_data:
        alliances.append(Alliance(code=code, name=name))

    for code, name in airlines_data:
        airlines.append(Airline(code=code, name=name))

    meta = JsMetadata(alliances=alliances, airlines=airlines)

    flights = MetaList()
    for k in data[3][0]:
        flight = k[0]

        typ = flight[0]
        airlines = flight[1]

        sg_flights = []

        # multiple flights!
        for single_flight in flight[2]:
            from_airport = Airport(code=single_flight[3], name=single_flight[4])
            to_airport = Airport(code=single_flight[6], name=single_flight[5])
            departure_time = single_flight[8]
            departure_date = single_flight[20]
            departure = SimpleDatetime(date=departure_date, time=departure_time)

            arrival_time = single_flight[10]
            arrival_date = single_flight[21]
            arrival = SimpleDatetime(date=arrival_date, time=arrival_time)

            plane_type = single_flight[17]

            duration = single_flight[11]

            sg_flights.append(
                JsSingleFlight(
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
            JsFlights(
                typ=typ,
                airlines=airlines,
                flights=sg_flights,
                carbon=JsCarbonEmission(
                    typical_on_route=typical_carbon_emission, emission=carbon_emission
                ),
            )
        )

    flights.metadata = meta
    return flights
