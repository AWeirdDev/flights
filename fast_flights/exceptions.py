"""Custom exceptions for the fast_flights package."""

class FastFlightsError(Exception):
    """Base exception for all fast_flights exceptions."""
    pass

class ValidationError(FastFlightsError, ValueError):
    """Raised when input validation fails."""
    pass

class AirportCodeError(ValidationError):
    """Raised when an invalid airport code is provided."""
    pass

class DateFormatError(ValidationError):
    """Raised when a date string is in an invalid format."""
    pass

class PassengerError(ValidationError):
    """Raised when there's an issue with passenger configuration."""
    pass

class FlightQueryError(ValidationError):
    """Raised when there's an issue with flight query parameters."""
    pass

class APIConnectionError(FastFlightsError):
    """Raised when there's an issue connecting to the flight data API."""
    pass

class APIError(FastFlightsError):
    """Raised when the flight data API returns an error."""
    pass
