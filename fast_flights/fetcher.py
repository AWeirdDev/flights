import logging
from typing import Optional, Union, overload

from primp import Client

from .exceptions import APIConnectionError, APIError
from .querying import Query
from .parser import MetaList, parse
from .integrations import Integration

# Set up logging
logger = logging.getLogger(__name__)

URL = "https://www.google.com/travel/flights"


@overload
def get_flights(q: str, /, *, proxy: Optional[str] = None):
    """Get flights using a str query.

    Examples:
    - *Flights from TPE to MYJ on 2025-12-22 one way economy class*
    """


@overload
def get_flights(q: Query, /, *, proxy: Optional[str] = None):
    """Get flights using a structured query.

    Example:
    ```python
    get_flights(
        query(
            flights=[
                FlightQuery(
                    date="2025-12-22",
                    from_airport="TPE",
                    to_airport="MYJ",
                )
            ],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="",
        )
    )
    ```
    """


def get_flights(
    q: Union[Query, str],
    /,
    *,
    proxy: Optional[str] = None,
    integration: Optional[Integration] = None,
) -> MetaList:
    """Get flights.

    Args:
        q: The query string or Query object.
        proxy: Optional proxy configuration.
        integration: Optional integration to use for fetching data.
        
    Returns:
        MetaList: Parsed flight data.
        
    Raises:
        APIConnectionError: If there's an issue connecting to the flight data source.
        APIError: If the API returns an error or invalid response.
        ValueError: If the input query is invalid.
    """
    try:
        logger.debug("Fetching flight data...")
        html = fetch_flights_html(q, proxy=proxy, integration=integration)
        if not html or not isinstance(html, str):
            raise APIError("Received empty or invalid response from the flight data source")
        return parse(html)
    except Exception as e:
        if isinstance(e, (APIConnectionError, APIError, ValueError)):
            raise
        raise APIConnectionError(f"Failed to fetch flight data: {str(e)}") from e


def fetch_flights_html(
    q: Union[Query, str],
    /,
    *,
    proxy: Optional[str] = None,
    integration: Optional[Integration] = None,
) -> str:
    """Fetch flights and get the HTML response.

    Args:
        q: The query string or Query object.
        proxy: Optional proxy configuration.
        integration: Optional integration to use for fetching data.
        
    Returns:
        str: The HTML content of the flight search results.
        
    Raises:
        APIConnectionError: If there's an issue connecting to the flight data source.
        APIError: If the API returns an error or invalid response.
        ValueError: If the input query is invalid.
    """
    if not q:
        raise ValueError("Query cannot be empty")
    
    try:
        if integration is None:
            logger.debug("Using default client for fetching flight data")
            client = Client(
                impersonate="chrome_133",
                impersonate_os="macos",
                referer=True,
                proxy=proxy,
                cookie_store=True,
                timeout=30,  # 30 seconds timeout
            )

            try:
                if isinstance(q, Query):
                    params = q.params()
                else:
                    if not isinstance(q, str):
                        raise ValueError("Query must be a string or Query object")
                    params = {"q": q}

                logger.debug(f"Sending request to {URL} with params: {params}")
                res = client.get(URL, params=params)
                
                # Check status code directly since primp's client might not have raise_for_status
                if res.status_code >= 400:
                    error_msg = f"Flight data API returned status code {res.status_code}"
                    logger.error(error_msg)
                    raise APIError(error_msg)
                
                if not res.text:
                    error_msg = "Received empty response from the flight data source"
                    logger.error(error_msg)
                    raise APIError(error_msg)
                    
                return res.text
                
            except APIError:
                # Re-raise APIError as is
                raise
            except ValueError as e:
                # Re-raise ValueError as is
                logger.error(f"Invalid query: {str(e)}")
                raise
            except Exception as e:
                # Handle other exceptions
                error_msg = f"Failed to connect to flight data source: {str(e)}"
                logger.error(error_msg)
                raise APIConnectionError(error_msg) from e

        else:
            logger.debug("Using integration for fetching flight data")
            try:
                return integration.fetch_html(q)
            except Exception as e:
                logger.error(f"Integration error while fetching flight data: {str(e)}")
                raise APIError(f"Integration failed to fetch flight data: {str(e)}") from e
                
    except Exception as e:
        if isinstance(e, (APIConnectionError, APIError, ValueError)):
            raise
        raise APIConnectionError(f"Unexpected error while fetching flight data: {str(e)}") from e
