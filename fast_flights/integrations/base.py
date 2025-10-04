"""Base integration module for flight data providers."""
import logging
import os
from abc import ABC, abstractmethod
from typing import Union, Optional

from ..exceptions import APIConnectionError, APIError
from ..querying import Query

# Set up logging
logger = logging.getLogger(__name__)

try:
    import dotenv  # pip install python-dotenv
    dotenv.load_dotenv()
except ModuleNotFoundError:
    logger.debug("python-dotenv not installed, skipping .env file loading")


class Integration(ABC):
    """Abstract base class for flight data integrations.
    
    This class defines the interface that all flight data integrations must implement.
    Subclasses should implement the fetch_html method to retrieve flight data.
    """
    
    @abstractmethod
    def fetch_html(self, q: Union[Query, str], /) -> str:
        """Fetch the flights page HTML from a query.

        Args:
            q: The query string or Query object.
                
        Returns:
            str: The HTML content of the flight search results.
            
        Raises:
            APIConnectionError: If there's an issue connecting to the data source.
            APIError: If the API returns an error or invalid response.
            ValueError: If the input query is invalid.
        """
        raise NotImplementedError("Subclasses must implement this method")


def get_env(k: str, /, default: Optional[str] = None) -> str:
    """Get environment variable with optional default value.
    
    Args:
        k: The name of the environment variable.
        default: Default value to return if the environment variable is not found.
                If not provided, raises an OSError when the variable is not found.
                
    Returns:
        str: The value of the environment variable, or the default value if provided.
        
    Raises:
        OSError: If the environment variable is not found and no default is provided.
    """
    value = os.environ.get(k, default)
    if value is None:
        error_msg = f"Required environment variable not found: {k!r}"
        logger.error(error_msg)
        raise OSError(error_msg)
    return value
