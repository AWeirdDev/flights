from dataclasses import dataclass
from typing import Literal

import rjsonc
from selectolax.lexbor import LexborHTMLParser

from .model import Airline, Alliance, Metadata


def parse(html: str, *, source: Literal["js", "html"] = "js"):
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
    alliances_data, airlines_data = data[7][1]

    for code, name in alliances_data:
        alliances.append(Alliance(code=code, name=name))

    for code, name in airlines_data:
        airlines.append(Airline(code=code, name=name))

    return Metadata(alliances=alliances, airlines=airlines)
