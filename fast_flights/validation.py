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

def validate_airport_code(code: str) -> str:
    """Validate and normalize an airport IATA code.
    
    Args:
        code: The airport code to validate.
        
    Returns:
        str: The normalized uppercase airport code.
        
    Raises:
        TypeError: If code is not a string.
        AirportCodeError: If the airport code format is invalid.
    """
    if not isinstance(code, str):
        raise TypeError(f"Airport code must be a string, got {type(code).__name__}")
    
    code = code.strip().upper()
    if not code:
        raise AirportCodeError("Airport code cannot be empty")
        
    if not re.match(r'^[A-Z]{3}$', code):
        raise AirportCodeError(f"Invalid IATA code: '{code}'. Must be 3 uppercase letters")
    
    return code

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
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0
) -> None:
    """Validate passenger configuration.
    
    Args:
        adults: Number of adults (must be >= 1).
        children: Number of children (must be >= 0).
        infants_in_seat: Number of infants with their own seat (must be >= 0).
        infants_on_lap: Number of infants on lap (must be >= 0).
        
    Raises:
        PassengerError: If passenger configuration is invalid.
        TypeError: If any count is not an integer.
        ValueError: If any count is negative.
    """
    # Validate input types and non-negative values
    for count, name in [
        (adults, "adults"),
        (children, "children"),
        (infants_in_seat, "infants_in_seat"),
        (infants_on_lap, "infants_on_lap")
    ]:
        if not isinstance(count, int):
            raise TypeError(f"{name} must be an integer, got {type(count).__name__}")
        if count < 0:
            raise ValueError(f"{name} cannot be negative")
    
    total = adults + children + infants_in_seat + infants_on_lap

    if adults < 1 and total > 0:
        raise PassengerError("At least one adult is required when traveling with passengers")
    
    if total > 9:
        raise PassengerError(f"Maximum of 9 passengers allowed, got {total}")
    
    if infants_on_lap > adults:
        raise PassengerError(
            f"Number of infants on lap ({infants_on_lap}) exceeds number of adults ({adults})"
        )

def validate_flight_query(
    from_airport: str,
    to_airport: str,
    date: Union[str, datetime],
    max_stops: Optional[int] = None
) -> tuple[str, str]:
    """Validate and normalize flight query parameters.
    
    Args:
        from_airport: Departure airport code.
        to_airport: Arrival airport code.
        date: Departure date (string in YYYY-MM-DD format or datetime object).
        max_stops: Maximum number of stops allowed.
        
    Returns:
        tuple: Normalized (from_airport, to_airport) codes.
        
    Raises:
        FlightQueryError: If any parameter is invalid.
    """
    # Validate and normalize airport codes
    from_code = validate_airport_code(from_airport)
    to_code = validate_airport_code(to_airport)
    
    # Ensure origin and destination are different
    if from_code == to_code:
        raise FlightQueryError("Origin and destination airports cannot be the same")
    
    # Validate date
    validate_date(date)
    
    # Validate max_stops if provided
    if max_stops is not None and (not isinstance(max_stops, int) or max_stops < 0):
        raise FlightQueryError("max_stops must be a non-negative integer")
    
    return from_code, to_code

def validate_currency(currency: str) -> str:
    """Validate and normalize a currency code.
    
    Args:
        currency: The currency code to validate (3-letter ISO code).
        
    Returns:
        str: The normalized uppercase currency code.
        
    Raises:
        TypeError: If currency is not a string.
        ValueError: If the currency code format is invalid.
    """
    if not isinstance(currency, str):
        raise TypeError(f"Currency must be a string, got {type(currency).__name__}")
    
    currency = currency.strip().upper()
    if not currency:
        raise ValueError("Currency code cannot be empty")
        
    if not re.match(r'^[A-Z]{3}$', currency):
        raise ValueError(
            f"Invalid currency code: '{currency}'. Must be 3 uppercase letters (e.g., 'USD', 'EUR')"
        )
    
    return currency
