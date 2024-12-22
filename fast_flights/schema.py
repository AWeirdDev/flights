from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from selectolax.lexbor import LexborHTMLParser


@dataclass
class Passengers:
    adults: int = 1
    children: int = 0
    infants_in_seat: int = 0
    infants_on_lap: int = 0


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


@dataclass
class Result:
    current_price: str
    flights: List[Flight]
    table: Optional[str] = None

    @classmethod
    def from_html(cls, parser: LexborHTMLParser) -> "Result":
        """Parse HTML response and create a Result object"""
        flights = []
        flight_elements = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
        price_elements = parser.css(".YMlIz.FpEdX")

        if not flight_elements or not price_elements:
            return cls(current_price="typical", flights=[])

        for i, fl in enumerate(flight_elements):
            is_best_flight = i == 0
            flight_items = fl.css("ul.Rk10dc li")

            for item in flight_items:
                # Flight name
                name = item.css_first("div.sSHqwe.tPgKwe.ogfYpf span")
                if not name:
                    continue
                name = name.text(strip=True)

                # Get departure & arrival time
                dp_ar_node = item.css("span.mv1WYe div")
                try:
                    departure_time = dp_ar_node[0].text(strip=True)
                    arrival_time = dp_ar_node[1].text(strip=True)
                except IndexError:
                    continue

                # Get arrival time ahead
                time_ahead = item.css_first("span.bOzv6")
                time_ahead = time_ahead.text() if time_ahead else ""

                # Get duration
                duration = item.css_first("li div.Ak5kof div")
                if not duration:
                    continue
                duration = duration.text()

                # Get flight stops
                stops_elem = item.css_first(".BbR8Ec .ogfYpf")
                stops = stops_elem.text() if stops_elem else "Nonstop"

                # Get delay
                delay_elem = item.css_first(".GsCCve")
                delay = delay_elem.text() if delay_elem else None

                # Get prices
                price_elem = item.css_first(".YMlIz.FpEdX")
                if not price_elem:
                    continue
                price = price_elem.text()

                # Stops formatting
                try:
                    stops_fmt = 0 if stops == "Nonstop" else int(stops.split(" ", 1)[0])
                except ValueError:
                    stops_fmt = 0

                flights.append(
                    Flight(
                        is_best=is_best_flight,
                        name=name,
                        departure=" ".join(departure_time.split()),
                        arrival=" ".join(arrival_time.split()),
                        arrival_time_ahead=time_ahead,
                        duration=duration,
                        stops=stops_fmt,
                        delay=delay,
                        price=price.replace(",", ""),
                    )
                )

        # Get current price indicator
        price_indicator = parser.css_first("span.gOatQ")
        price_indicator = (
            price_indicator.text().lower() if price_indicator else "typical"
        )

        if "low" in price_indicator:
            current_price = "low"
        elif "high" in price_indicator:
            current_price = "high"
        else:
            current_price = "typical"

        return cls(current_price=current_price, flights=flights)
