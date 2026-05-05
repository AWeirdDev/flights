import json

import pytest

from fast_flights import FetchResult
from fast_flights.parser import parse


def _flight_row(price=380, airline="American", code="AA"):
    single = [None] * 25
    single[3] = "RDU"
    single[4] = "Raleigh-Durham International Airport"
    single[5] = "Adolfo Suarez Madrid-Barajas Airport"
    single[6] = "MAD"
    single[8] = [7, 15]
    single[10] = [20, 45]
    single[11] = 450
    single[17] = "Boeing 777"
    single[20] = [2026, 8, 1]
    single[21] = [2026, 8, 1]

    flight = [None] * 25
    flight[0] = code
    flight[1] = [airline]
    flight[2] = [single]
    flight[22] = [None, None, None, None, None, None, None, 542000, 498000]
    return [flight, [[None, price]]]


def _payload(rows):
    data = [None] * 8
    data[3] = [rows]
    data[7] = [
        None,
        [
            [["ONEWORLD", "Oneworld"]],
            [["AA", "American"]],
        ],
    ]
    return data


def _script_html(data):
    return (
        '<html><script class="ds:1">'
        f"AF_initDataCallback({{key: 'ds:1', data: {json.dumps(data)}, sideChannel: {{}}}});"
        "</script></html>"
    )


def _wrb_body(payload):
    frame = [["wrb.fr", None, json.dumps(payload)]]
    return ")]}'\n\n123\n" + json.dumps(frame)


def _error_body():
    return (
        ")]}'\n\n269\n"
        '[["wrb.fr",null,null,null,null,[3,null,'
        '[["type.googleapis.com/travel.frontend.flights.ErrorResponse",[]]]]]]'
    )


def _wrb_frame_body(frame):
    return ")]}'\n\n123\n" + json.dumps(frame)


def test_script_ds1_fixture_still_parses():
    result = parse(_script_html(_payload([_flight_row()])))

    assert len(result) == 1
    assert result[0].price == 380
    assert result[0].airlines == ["American"]
    assert result[0].flights[0].from_airport.code == "RDU"
    assert result.metadata.airlines[0].code == "AA"


def test_missing_script_returns_empty_with_diagnostic_metadata():
    result = parse("<html><body>No flights here</body></html>")

    assert result == []
    assert result.metadata.diagnostics["status"] == "missing_script_ds1"


def test_error_response_wrb_returns_empty_with_diagnostic_metadata():
    result = parse(FetchResult(html="", xhr_bodies=[_error_body()]))

    assert result == []
    assert result.metadata.diagnostics["status"] == "google_error_response"
    assert result.metadata.diagnostics["source"] == "xhr"


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ("not json", "malformed_xhr_body"),
        (_wrb_frame_body([["wrb.fr", None, "{bad"]]), "malformed_wrb_payload"),
        (_wrb_body(_payload([])), "empty_flight_payload"),
        (_wrb_frame_body([["wrb.fr", None, None]]), "no_parseable_xhr"),
    ],
)
def test_empty_xhr_results_include_diagnostic_metadata(body, status):
    result = parse(FetchResult(html="", xhr_bodies=[body]))

    assert result == []
    assert result.metadata.diagnostics["status"] == status
    assert result.metadata.diagnostics["source"] == "xhr"


def test_captured_wrb_payload_parses_existing_models():
    result = parse(
        FetchResult(
            html="<html></html>",
            xhr_bodies=[_wrb_body(_payload([_flight_row(426)]))],
        )
    )

    assert len(result) == 1
    assert result[0].price == 426
    assert result[0].carbon.emission == 542000
    assert result[0].flights[0].arrival.date == (2026, 8, 1)


def test_get_flights_uses_integration_xhr_payload():
    import fast_flights as ff

    class FakeQuery:
        pass

    class FakeIntegration:
        def fetch_html(self, q):
            return FetchResult(
                html="<html></html>",
                xhr_bodies=[_wrb_body(_payload([_flight_row(512)]))],
            )

    result = ff.get_flights(FakeQuery(), integration=FakeIntegration())

    assert len(result) == 1
    assert result[0].price == 512


def test_later_valid_xhr_wins_after_earlier_error_xhr():
    result = parse(
        FetchResult(
            html="<html></html>",
            xhr_bodies=[_error_body(), _wrb_body(_payload([_flight_row(614)]))],
        )
    )

    assert len(result) == 1
    assert result[0].price == 614
