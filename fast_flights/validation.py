"""Input validation utilities for fast_flights package."""
import re
from datetime import datetime
from enum import Enum
from typing import Any, List, Literal, Optional, Tuple, Type, TypeVar, Union, get_args, get_origin
from .exceptions import (
    AirportCodeError,
    DateFormatError,
    PassengerError,
    FlightQueryError
)
from .types import Language, SeatType, TripType, Currency

T = TypeVar('T')

def validate_enum_value(value: Any, enum_type: Type[T], field_name: str) -> T:
    """Validate that a value is a valid enum value or literal.
    
    Args:
        value: The value to validate.
        enum_type: The enum class or Literal type to validate against.
        field_name: The name of the field being validated (for error messages).
        
    Returns:
        The validated value.
        
    Raises:
        FlightQueryError: If the value is not a valid enum or literal value.
    """
    # Handle Enum types
    if isinstance(enum_type, type) and issubclass(enum_type, Enum):
        try:
            return enum_type(value)
        except ValueError:
            valid_values = [e.value for e in enum_type]
            raise FlightQueryError(
                f"Invalid {field_name}: '{value}'. "
                f"Must be one of: {', '.join(repr(v) for v in valid_values)}"
            ) from None
    
    # Handle Literal types
    origin = get_origin(enum_type)
    if origin is Literal:
        valid_values = get_args(enum_type)
        if value in valid_values:
            return value
        raise FlightQueryError(
            f"Invalid {field_name}: '{value}'. "
            f"Must be one of: {', '.join(repr(v) for v in valid_values)}"
        ) from None
    
    # Handle regular types
    if isinstance(value, enum_type):
        return value
        
    raise FlightQueryError(
        f"Expected {field_name} to be of type {enum_type.__name__}, got {type(value).__name__}"
    )

def validate_airport_code(code: str) -> str:
    """Validate and normalize an airport IATA code.
    
    Args:
        code: The airport code to validate.
        
    Returns:
        str: The normalized uppercase airport code.
        
    Raises:
        AirportCodeError: If the airport code is not a string or has an invalid format.
    """
    if not isinstance(code, str):
        raise AirportCodeError(f"Airport code must be a string, got {type(code).__name__}")
    
    code = code.strip().upper()
    if not code:
        raise AirportCodeError("Airport code cannot be empty")
    if not re.match(r'^[A-Z]{3}$', code):
        raise AirportCodeError(f"Invalid IATA code: '{code}'. Must be 3 uppercase letters")
    
    return code

def validate_passengers(
    adults: int,
    children: int,
    infants_in_seat: int,
    infants_on_lap: int,
    max_passengers: int = 9,
) -> None:
    """Validate passenger configuration for a flight booking.
    
    Ensures that the passenger configuration follows these rules:
    - At least one adult is required
    - No more than max_passengers (default: 9) total passengers allowed
    - Number of infants on lap cannot exceed number of adults
    - All counts must be non-negative integers
    
    Args:
        adults: Number of adults (must be >= 1).
        children: Number of children (must be >= 0).
        infants_in_seat: Number of infants with their own seat (must be >= 0).
        infants_on_lap: Number of infants on lap (must be >= 0).
        max_passengers: Maximum allowed total passengers (default: 9).
        
    Raises:
        PassengerError: If passenger configuration is invalid, counts are not integers,
            counts are negative, or other validation fails.
    """
    # Validate input types
    if not all(isinstance(x, int) for x in [adults, children, infants_in_seat, infants_on_lap]):
        raise PassengerError("All passenger counts must be integers")
    
    # Validate at least one adult
    if adults < 1:
        raise PassengerError("At least one adult is required")
    
    # Validate non-negative values
    if children < 0:
        raise PassengerError("Number of children cannot be negative")
    if infants_in_seat < 0:
        raise PassengerError("Number of infants in seat cannot be negative")
    if infants_on_lap < 0:
        raise PassengerError("Number of infants on lap cannot be negative")
    
    total = adults + children + infants_in_seat + infants_on_lap
    
    # Validate at least one passenger
    if total < 1:
        raise PassengerError("At least one passenger is required")
    


    # Validate total passengers
    if total > max_passengers:
        raise PassengerError(
            f"Maximum of {max_passengers} passengers allowed, got {total} "
            f"({adults} adults, {children} children, {infants_in_seat} infants in seat, "
            f"{infants_on_lap} infants on lap)"
        )
    
    # Validate infants on lap
    if infants_on_lap > 0 and adults < 1:
        raise PassengerError(
            f"Cannot have {infants_on_lap} infants on lap without at least one adult"
        )
    
    # Validate infants in seat
    if infants_in_seat > 0 and adults < 1 and children < 1:
        raise PassengerError(
            f"Cannot have {infants_in_seat} infants in seat without at least one adult or child"
        )

def validate_flight_query(
    from_airport: str,
    to_airport: str,
    date: Union[str, datetime],
    max_stops: Optional[int] = None
) -> tuple[str, str]:
    """Validate and normalize flight query parameters.
    
    Validates that:
    - Airport codes are valid IATA codes
    - Origin and destination are different
    - Date is valid and in the future
    - max_stops is a non-negative integer or None
    
    Args:
        from_airport: Departure airport code (case-insensitive).
        to_airport: Arrival airport code (case-insensitive).
        date: Departure date (string in YYYY-MM-DD format or datetime object).
        max_stops: Maximum number of stops allowed (None for no limit).
        
    Returns:
        tuple: Normalized (from_airport, to_airport) codes in uppercase.
        
    Raises:
        FlightQueryError: If any parameter is invalid.
        AirportCodeError: If airport codes are invalid.
        DateFormatError: If date format is invalid or in the past.
    """
    # Validate and normalize airport codes
    from_airport_norm = validate_airport_code(from_airport)
    to_airport_norm = validate_airport_code(to_airport)
    
    # Ensure origin and destination are different
    if from_airport_norm == to_airport_norm:
        raise FlightQueryError(
            f"Origin and destination airports cannot be the same: {from_airport_norm}"
        )
    
    # Validate date is in the future
    normalized_date = validate_and_normalize_date(date)
    today = datetime.now().date()
    if isinstance(normalized_date, str):
        normalized_date = datetime.strptime(normalized_date, "%Y-%m-%d").date()
    
    if normalized_date < today:
        raise DateFormatError("Departure date cannot be in the past")
    
    # Validate max_stops
    if max_stops is not None:
        if not isinstance(max_stops, int):
            raise FlightQueryError("max_stops must be an integer or None")
        if max_stops < 0:
            raise FlightQueryError("max_stops cannot be negative")
    
    return from_airport_norm, to_airport_norm

def _validate_literal(value: Any, literal_type: Type[T], type_name: str) -> T:
    """Validate a value against a Literal type or Enum.
    
    Args:
        value: The value to validate.
        literal_type: The type to validate against (Literal or Enum).
        type_name: Human-readable name of the type for error messages.
        
    Returns:
        The validated value of type T.
        
    Raises:
        FlightQueryError: If the value is not a valid value of the literal type.
    """
    # Handle Enum types
    if isinstance(literal_type, type) and issubclass(literal_type, Enum):
        try:
            return literal_type(value)
        except ValueError:
            valid_values = [e.value for e in literal_type]
            raise FlightQueryError(
                f"Invalid {type_name}: '{value}'. "
                f"Must be one of: {', '.join(repr(v) for v in valid_values)}"
            ) from None
    
    # Handle Literal types
    origin = get_origin(literal_type)
    if origin is Literal:
        valid_values = get_args(literal_type)
        if value in valid_values:
            return value
        raise FlightQueryError(
            f"Invalid {type_name}: '{value}'. "
            f"Must be one of: {', '.join(repr(v) for v in valid_values)}"
        )
    
    # If we get here, the type is not supported
    raise ValueError(f"Unsupported type for validation: {literal_type}")


def validate_seat_type(seat: Union[str, SeatType]) -> SeatType:
    """Validate that a seat type is valid.
    
    Args:
        seat: The seat type to validate.
        
    Returns:
        SeatType: The validated seat type.
        
    Raises:
        FlightQueryError: If the seat type is invalid.
    """
    return _validate_literal(seat, SeatType, 'seat type')


def validate_trip_type(trip: Union[str, TripType]) -> TripType:
    """Validate that a trip type is valid.
    
    Args:
        trip: The trip type to validate.
        
    Returns:
        TripType: The validated trip type.
        
    Raises:
        FlightQueryError: If the trip type is invalid.
    """
    return _validate_literal(trip, TripType, 'trip type')


def validate_language(language: Union[str, Language, None]) -> str:
    """Validate and normalize a language code.
    
    Args:
        language: The language code to validate.
        
    Returns:
        str: The normalized language code, or empty string if None.
        
    Raises:
        FlightQueryError: If the language code is invalid.
    """
    if language is None:
        return ""
    language_str = str(language).strip()
    if not language_str:
        return ""  # Empty string is allowed (means use default)
        
    return _validate_literal(language_str, Language, 'language code')


def validate_currency(currency: Union[str, Currency, None]) -> str:
    """Validate and normalize a currency code.
    
    Args:
        currency: The currency code to validate.
        
    Returns:
        str: The normalized currency code, or empty string if None.
        
    Raises:
        FlightQueryError: If the currency code is invalid.
    """
    if currency is None:
        return ""
        
    currency_str = str(currency).strip().upper()
    if not currency_str:
        return ""  # Empty string is allowed (means use default)
        
    return _validate_literal(currency_str, Currency, 'currency code')


def validate_flights_list(flights: List[Any], expected_type: Type[T]) -> List[T]:
    """Validate that a list contains only instances of the expected type.
        flights: The list to validate.
        expected_type: The expected type of list elements.
        
    Returns:
        List[T]: The validated list.
        
    Raises:
        FlightQueryError: If the list is empty or contains invalid elements.
    """
    if not isinstance(flights, (list, tuple)) or not flights:
        raise FlightQueryError("At least one flight segment is required")
    
    if not all(isinstance(f, expected_type) for f in flights):
        type_name = expected_type.__name__
        raise FlightQueryError(f"All flight segments must be {type_name} instances")
    
    return flights  # type: ignore


def validate_airline_code(code: str) -> str:
    """Validate and normalize an airline IATA code.
    
    Args:
        code: The airline code to validate.
        
    Returns:
        str: The normalized uppercase airline code.
        
    Raises:
        FlightQueryError: If the airline code format is invalid.
    """
    if not isinstance(code, str):
        raise FlightQueryError(f"Airline code must be a string, got {type(code).__name__}")
    
    code = code.strip().upper()
    if not code:
        raise FlightQueryError("Airline code cannot be empty")
        
    if not re.match(r'^[A-Z]{2}$', code):
        raise FlightQueryError(
            f"Invalid airline code: '{code}'. Must be 2 uppercase letters"
        )
    
    return code


def validate_and_normalize_date(date: Union[str, datetime]) -> str:
    """Validate and normalize a date to YYYY-MM-DD format.
    
    Args:
        date: The date to validate, either as a string in YYYY-MM-DD format or a datetime object.
        
    Returns:
        str: The normalized date string in YYYY-MM-DD format.
        
    Raises:
        DateFormatError: If the date format is invalid.
    """
    if isinstance(date, str):
        try:
            # Try to parse the string to validate it
            datetime.strptime(date, '%Y-%m-%d')
            return date
        except ValueError as e:
            raise DateFormatError(
                f"Invalid date format: '{date}'. Expected YYYY-MM-DD"
            ) from e
    elif isinstance(date, datetime):
        return date.strftime('%Y-%m-%d')
    else:
        raise DateFormatError(
            f"Date must be a string or datetime object, got {type(date).__name__}"
        )


def validate_max_stops(max_stops: Optional[int]) -> Optional[int]:
    """Validate the max_stops parameter.
    
    Args:
        max_stops: Maximum number of stops allowed, or None for any number of stops.
        
    Returns:
        Optional[int]: The validated max_stops value.
        
    Raises:
        FlightQueryError: If max_stops is not a non-negative integer.
    """
    if max_stops is not None:
        if not isinstance(max_stops, int) or max_stops < 0:
            raise FlightQueryError("max_stops must be a non-negative integer")
    return max_stops


def validate_airlines(airlines: Optional[list[str]]) -> Optional[list[str]]:
    """Validate a list of airline IATA codes.
    
    Args:
        airlines: List of airline codes to validate. Can be None.
        
    Returns:
        Optional[list[str]]: List of normalized airline codes, or None if input was None.
        
    Raises:
        FlightQueryError: If any airline code is invalid or input is not a list.
    """
    if airlines is None:
        return None
        
    if not isinstance(airlines, list):
        raise FlightQueryError("Airlines must be a list of 2-letter IATA codes")
        
    if not airlines:  # Empty list is valid (means no airline filter)
        return None
    
    try:
        return [validate_airline_code(code) for code in airlines]
    except ValueError as e:
        raise FlightQueryError(str(e)) from e
    
