"""Input validation utilities for fast_flights package."""
import re
from datetime import datetime
from typing import Optional, Union

from .exceptions import (
    AirportCodeError,
    DateFormatError,
    PassengerError,
    FlightQueryError
)

def validate_airport_code(code: str) -> None:
    """Validate an airport IATA code.
    
    Args:
        code: The airport code to validate.
        
    Raises:
        AirportCodeError: If the airport code is invalid.
    """
    if not isinstance(code, str):
        raise AirportCodeError(f"Airport code must be a string, got {type(code).__name__}")
    
    if not re.match(r'^[A-Z]{3}$', code.upper()):
        raise AirportCodeError(
            f"Invalid airport code: {code}. Must be 3 uppercase letters (IATA code)"
        )

def validate_date(date_str: Union[str, datetime]) -> None:
    """Validate a date string or datetime object.
    
    Args:
        date_str: The date to validate (string in YYYY-MM-DD format or datetime object).
        
    Raises:
        DateFormatError: If the date format is invalid.
    """
    if isinstance(date_str, datetime):
        return
        
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except (TypeError, ValueError) as e:
        raise DateFormatError(
            f"Invalid date format: {date_str}. Expected YYYY-MM-DD or datetime object"
        ) from e

def validate_passengers(
    adults: int = 0,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0
) -> None:
    """Validate passenger configuration.
    
    Args:
        adults: Number of adults.
        children: Number of children.
        infants_in_seat: Number of infants with their own seat.
        infants_on_lap: Number of infants on lap.
        
    Raises:
        PassengerError: If passenger configuration is invalid.
    """
    total = sum((adults, children, infants_in_seat, infants_on_lap))
    
    if total > 9:
        raise PassengerError(f"Too many passengers ({total} > 9)")
    
    if adults < 1 and (children > 0 or infants_in_seat > 0 or infants_on_lap > 0):
        raise PassengerError("At least one adult is required when traveling with children or infants")
    
    if infants_on_lap > adults:
        raise PassengerError(
            f"Number of infants on lap ({infants_on_lap}) exceeds number of adults ({adults})"
        )

def validate_flight_query(
    from_airport: str,
    to_airport: str,
    date: Union[str, datetime],
    max_stops: Optional[int] = None
) -> None:
    """Validate flight query parameters.
    
    Args:
        from_airport: Departure airport code.
        to_airport: Arrival airport code.
        date: Departure date (string in YYYY-MM-DD format or datetime object).
        max_stops: Maximum number of stops allowed.
        
    Raises:
        FlightQueryError: If any parameter is invalid.
    """
    # Validate airport codes
    try:
        validate_airport_code(from_airport)
        validate_airport_code(to_airport)
    except AirportCodeError as e:
        raise FlightQueryError(f"Invalid airport code: {e}")
    
    # Ensure origin and destination are different
    if from_airport.upper() == to_airport.upper():
        raise FlightQueryError("Origin and destination airports cannot be the same")
    
    # Validate date
    try:
        validate_date(date)
    except DateFormatError as e:
        raise FlightQueryError(f"Invalid date: {e}")
    
    # Validate max_stops if provided
    if max_stops is not None and (not isinstance(max_stops, int) or max_stops < 0):
        raise FlightQueryError("max_stops must be a non-negative integer")

def validate_currency(currency: str) -> None:
    """Validate currency code.
    
    Args:
        currency: The currency code to validate (3-letter ISO code).
        
    Raises:
        ValueError: If the currency code is invalid.
    """
    if not isinstance(currency, str):
        raise ValueError(f"Currency must be a string, got {type(currency).__name__}")
    
    if currency and not re.match(r'^[A-Z]{3}$', currency.upper()):
        raise ValueError(
            f"Invalid currency code: {currency}. Must be a 3-letter ISO code (e.g., 'USD', 'EUR')"
        )
