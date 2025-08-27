import os
from typing import Any
from .primp import Client


def bright_data_fetch(params: dict) -> Any:
    # Read environment variables with defaults
    api_url = os.environ.get("BRIGHT_DATA_API_URL", "https://api.brightdata.com/request")
    api_key = os.environ.get("BRIGHT_DATA_API_KEY")  # Required, no default
    zone = os.environ.get("BRIGHT_DATA_SERP_ZONE", "serp_api1")
    
    if not api_key:
        raise ValueError("BRIGHT_DATA_API_KEY environment variable is required")
    
    # Construct Google Flights URL
    url = "https://www.google.com/travel/flights?" + "&".join(f"{k}={v}" for k, v in params.items())
    
    # Make request to Bright Data (no impersonation needed - Bright Data handles it)
    client = Client(verify=False)
    res = client.post(
        api_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={"url": url, "zone": zone}
    )
    
    assert res.status_code == 200, f"{res.status_code} Result: {res.text}"
    
    # Return DummyResponse with HTML content
    class DummyResponse:
        status_code = 200
        text = res.text  # Bright Data returns raw HTML
        text_markdown = text
    
    return DummyResponse