"""Tests for validation functions."""
import pytest
from enum import Enum
from typing import Literal
from datetime import datetime, timedelta
from fast_flights.validation import (
    validate_enum_value,
    validate_language,
    validate_currency,
    validate_seat_type,
    validate_trip_type,
    validate_flight_query,
    FlightQueryError,
    AirportCodeError,
    DateFormatError
)
from fast_flights.types import Language, SeatType, TripType, Currency


def test_validate_enum_value_with_enum():
    """Test validation with Python enums."""
    class TestEnum(Enum):
        A = "A"
        B = "B"
    
    # Valid enum values
    assert validate_enum_value("A", TestEnum, "test_field") == TestEnum.A
    assert validate_enum_value(TestEnum.B, TestEnum, "test_field") == TestEnum.B
    
    # Invalid enum value
    with pytest.raises(FlightQueryError) as excinfo:
        validate_enum_value("C", TestEnum, "test_field")
    assert "Invalid test_field: 'C'" in str(excinfo.value)


def test_validate_enum_value_with_literal():
    """Test validation with Literal types."""
    TestLiteral = Literal["X", "Y", "Z"]
    
    # Valid literal values
    assert validate_enum_value("X", TestLiteral, "test_field") == "X"
    assert validate_enum_value("Y", TestLiteral, "test_field") == "Y"
    
    # Invalid literal value
    with pytest.raises(FlightQueryError) as excinfo:
        validate_enum_value("W", TestLiteral, "test_field")
    assert "Invalid test_field: 'W'" in str(excinfo.value)


def test_validate_language():
    """Test language code validation."""
    # Valid languages
    assert validate_language("en-US") == "en-US"
    assert validate_language("fr") == "fr"
    assert validate_language("zh-CN") == "zh-CN"
    
    # Invalid languages
    with pytest.raises(FlightQueryError):
        validate_language("invalid")
    with pytest.raises(FlightQueryError):
        validate_language("en-US-extra")
    
    # None case
    assert validate_language(None) == ""


def test_validate_currency():
    """Test currency code validation."""
    # Valid currencies
    assert validate_currency("USD") == "USD"
    assert validate_currency("EUR") == "EUR"
    
    # Invalid currencies
    with pytest.raises(FlightQueryError):
        validate_currency("US")
    with pytest.raises(FlightQueryError):
        validate_currency("USDD")
    with pytest.raises(FlightQueryError):
        validate_currency("123")
    
    # None case


def test_validate_seat_type():
    """Test seat type validation."""
    # Valid seat types
    assert validate_seat_type("economy") == "economy"
    assert validate_seat_type("premium-economy") == "premium-economy"
    assert validate_seat_type("business") == "business"
    assert validate_seat_type("first") == "first"
    assert validate_seat_type("economy") == "economy"  # Test with string value
    
    # Invalid seat type
    with pytest.raises(FlightQueryError) as excinfo:
        validate_seat_type("invalid")
    assert "seat type" in str(excinfo.value).lower()


def test_validate_trip_type():
    """Test trip type validation."""
    # Valid trip types
    assert validate_trip_type("one-way") == "one-way"
    assert validate_trip_type("round-trip") == "round-trip"
    assert validate_trip_type("multi-city") == "multi-city"
    
    # Invalid trip types
    with pytest.raises(FlightQueryError) as excinfo:
        validate_trip_type("invalid")
    assert "trip type" in str(excinfo.value).lower()
    
    with pytest.raises(FlightQueryError):
        validate_trip_type(123)


def test_validate_flight_query():
    """Test flight query validation."""
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Valid query
    from_airport, to_airport = validate_flight_query("JFK", "LAX", future_date, 2)
    assert from_airport == "JFK"
    assert to_airport == "LAX"
    
    # Same origin and destination
    with pytest.raises(FlightQueryError):
        validate_flight_query("JFK", "JFK", future_date)
    
    # Past date
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    with pytest.raises(DateFormatError):
        validate_flight_query("JFK", "LAX", past_date)
    
    # Invalid airport codes
    with pytest.raises(AirportCodeError):
        validate_flight_query("JK", "LAX", future_date)
    with pytest.raises(AirportCodeError):
        validate_flight_query("JFK", "LONG", future_date)
    
    # Invalid max_stops
    with pytest.raises(FlightQueryError):
        validate_flight_query("JFK", "LAX", future_date, -1)
    with pytest.raises(FlightQueryError):
        validate_flight_query("JFK", "LAX", future_date, "two")
