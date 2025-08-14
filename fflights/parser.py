from typing import Literal
import rjsonc
from selectolax.lexbor import LexborHTMLParser


def parse(html: str, *, source: Literal["js", "html"] = "js"):
    parser = LexborHTMLParser(html)

    # find js
    script = parser.css_first(r"script.ds\:1")
    parse_js(script.text())


def parse_js(js: str):
    json = js.split("data:", 1)[1].rstrip("); ")
    data = rjsonc.loads(json)
    print(data)
