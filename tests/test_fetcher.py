from fast_flights.fetch_result import FetchResult
from fast_flights.fetcher import get_flights

from tests.test_parser import _flight_row, _payload, _wrb_body


class FakeQuery:
    def params(self):
        return {"tfs": "fake"}


class XhrIntegration:
    def fetch_html(self, q):
        return FetchResult(
            html="<html></html>",
            xhr_bodies=[_wrb_body(_payload([_flight_row(512)]))],
        )


class HtmlIntegration:
    def fetch_html(self, q):
        data = _payload([_flight_row(300)])
        import json

        return (
            '<html><script class="ds:1">'
            f"AF_initDataCallback({{data: {json.dumps(data)}}});"
            "</script></html>"
        )


def test_get_flights_accepts_integration_with_captured_xhr():
    result = get_flights(FakeQuery(), integration=XhrIntegration())

    assert len(result) == 1
    assert result[0].price == 512


def test_get_flights_still_accepts_html_only_integration():
    result = get_flights(FakeQuery(), integration=HtmlIntegration())

    assert len(result) == 1
    assert result[0].price == 300
