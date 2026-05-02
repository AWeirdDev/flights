import json

from fast_flights.fetch_result import FetchResult
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


def test_script_ds1_payload_still_parses():
    result = parse(_script_html(_payload([_flight_row()])))

    assert len(result) == 1
    assert result[0].price == 380
    assert result[0].airlines == ["American"]
    assert result[0].flights[0].from_airport.code == "RDU"
    assert result.metadata.airlines[0].code == "AA"


def test_missing_script_ds1_returns_empty_metalist():
    result = parse("<html><body>No embedded data</body></html>")

    assert result == []
    assert result.metadata.diagnostics["status"] == "missing_script_ds1"


def test_google_error_response_wrb_returns_empty_with_diagnostics():
    error_body = (
        ")]}'\n\n269\n"
        '[["wrb.fr",null,null,null,null,[3,null,'
        '[["type.googleapis.com/travel.frontend.flights.ErrorResponse",[]]]]]]'
    )

    result = parse(FetchResult(html="", xhr_bodies=[error_body]))

    assert result == []
    assert result.metadata.diagnostics == {
        "status": "google_error_response",
        "source": "xhr",
    }


def test_captured_wrb_payload_parses_models():
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


def test_xhr_payload_is_preferred_over_html_fallback():
    html = _script_html(_payload([_flight_row(999)]))
    result = parse(
        FetchResult(
            html=html,
            xhr_bodies=[_wrb_body(_payload([_flight_row(512)]))],
        )
    )

    assert len(result) == 1
    assert result[0].price == 512
