"""Regression test for the BrightData integration's request body.

Doesn't need a real API key: mocks the underlying primp.Client so we can
assert on what gets sent, rather than what comes back.
"""

from unittest.mock import MagicMock, patch

from fast_flights.integrations.bright_data import BrightData
from fast_flights.querying import create_query, FlightQuery, Passengers


def _make_query():
    return create_query(
        flights=[FlightQuery(date="2026-01-01", from_airport="LAX", to_airport="JFK")],
        passengers=Passengers(adults=1),
    )


@patch("fast_flights.integrations.bright_data.Client")
def test_fetch_html_sends_required_format_field(mock_client_cls):
    # Bright Data's /request endpoint 400s with "\"format\" is required"
    # if this is omitted -- confirmed against a live account 2026-08-30.
    mock_client = MagicMock()
    mock_client.post.return_value.text = "<html></html>"
    mock_client_cls.return_value = mock_client

    bd = BrightData(api_key="test-key")
    bd.fetch_html(_make_query())

    _, kwargs = mock_client.post.call_args
    assert kwargs["json"]["format"] == "raw"


@patch("fast_flights.integrations.bright_data.Client")
def test_fetch_html_sends_required_format_field_for_str_query(mock_client_cls):
    mock_client = MagicMock()
    mock_client.post.return_value.text = "<html></html>"
    mock_client_cls.return_value = mock_client

    bd = BrightData(api_key="test-key")
    bd.fetch_html("flights from LAX to JFK on 2026-01-01")

    _, kwargs = mock_client.post.call_args
    assert kwargs["json"]["format"] == "raw"
