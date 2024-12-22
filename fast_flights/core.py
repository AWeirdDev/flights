from __future__ import annotations

import asyncio
import logging
import random
from typing import TYPE_CHECKING, Any, Dict, Optional

import aiohttp
from selectolax.lexbor import LexborHTMLParser

from .flights_impl import TFSData
from .schema import Result

if TYPE_CHECKING:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Common browser headers
BROWSER_HEADERS = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    },
]

# EU cookie consent
eu_cookies = {
    "CONSENT": "PENDING+987",
    "SOCS": "CAESHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmRlIAEaBgiAo_CmBg",
}


class Response:
    """Wrapper class to provide requests-like interface for aiohttp Response"""

    def __init__(self, aiohttp_response: aiohttp.ClientResponse, text: str):
        self._response = aiohttp_response
        self._text = text

    @property
    def content(self) -> bytes:
        return self._text.encode("utf-8")

    @property
    def cookies(self) -> Dict[str, str]:
        return {k: v.value for k, v in self._response.cookies.items()}

    @property
    def headers(self) -> Dict[str, str]:
        return dict(self._response.headers)

    @property
    def status_code(self) -> int:
        return self._response.status

    @property
    def text(self) -> str:
        return self._text

    @property
    def url(self) -> str:
        return str(self._response.url)

    def raise_for_status(self) -> None:
        """Raises an HTTPError for bad responses (4xx, 5xx)"""
        if self.status_code >= 400:
            raise Exception(
                f"HTTP {self.status_code} Error for url: {self.url}\n"
                f"Response: {self.text[:1000]}"
            )


async def make_request_with_retry(
    session: aiohttp.ClientSession,
    request_url: str,
    request_params: Dict[str, str],
    cookies: Dict[str, str],
    max_retries: int = 3,
    initial_delay: float = 5.0,
) -> Response:
    """Make request with retry mechanism"""
    last_error = None
    delay = initial_delay

    # Configure compression
    compression = aiohttp.ClientSession(
        headers=random.choice(BROWSER_HEADERS),
        cookies=cookies,
        timeout=aiohttp.ClientTimeout(total=30),
    )

    for attempt in range(max_retries):
        try:
            async with compression as session:
                async with session.get(
                    request_url,
                    params=request_params,
                ) as response:
                    text = await response.text()
                    wrapped_response = Response(response, text)
                    wrapped_response.raise_for_status()

                    logger.info(
                        f"response: {wrapped_response.url} {wrapped_response.status_code} {len(wrapped_response.text)}"
                    )

                    # Add delay between requests
                    await asyncio.sleep(delay)

                    return wrapped_response

        except Exception as e:
            last_error = e
            logger.warning(
                f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
            )

            # Exponential backoff with jitter
            delay = min(initial_delay * (2**attempt) + random.uniform(0, 1), 30.0)
            await asyncio.sleep(delay)

    raise last_error or Exception("All retry attempts failed")


async def get_flights(
    tfs: TFSData,
    *,
    max_stops: Optional[int] = None,
    currency: Optional[str] = None,
    language: Optional[str] = None,
    inject_eu_cookies: bool = False,
    **kwargs: Any,
) -> Result:
    """
    Get flights from Google Flights.
    This is an async version of the function that uses aiohttp.
    """
    # Ensure all parameters are properly encoded strings
    params = {
        "tfs": tfs.as_b64().decode("utf-8"),
        "hl": language or "en",
        "tfu": "EgQIABABIgA",  # show all flights and prices condition
    }

    # Add currency if specified
    if currency:
        params["curr"] = currency

    # Add EU cookies if requested
    cookies = eu_cookies if inject_eu_cookies else {}

    # Create aiohttp session with retry logic
    async with aiohttp.ClientSession() as session:
        response = await make_request_with_retry(
            session,
            "https://www.google.com/travel/flights",
            params,
            cookies,
        )

        # Parse HTML response
        parser = LexborHTMLParser(response.text)
        return Result.from_html(parser)
