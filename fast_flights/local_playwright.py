from typing import Any, Optional
import asyncio
from playwright.async_api import async_playwright

async def fetch_with_playwright(url: str, playwright_url: Optional[str] = None) -> str:
    """
    Fetch content from a URL using Playwright browser automation.
    
    Args:
        url: Target URL to fetch
        playwright_url: WebSocket endpoint (ws:// or wss://) for remote Playwright instance.
                       If None, launches local Chromium browser.
    
    Returns:
        HTML content from the page's main role element
    """
    async with async_playwright() as p:
        if playwright_url:
            # Connect to remote Playwright instance (e.g., Docker container)
            browser = await p.chromium.connect(playwright_url)
        else:
            # Launch local Chromium instance
            browser = await p.chromium.launch()
        
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        if page.url.startswith("https://consent.google.com"):
            await page.click('text="Accept all"')
        
        await page.wait_for_selector('[role="main"]', timeout=30000)
        body = await page.evaluate(
            "() => document.querySelector('[role=\"main\"]').innerHTML"
        )
        
        if not playwright_url:
            # Only close browser if we launched it locally
            # Remote browsers should be managed by their container
            await browser.close()
    return body

def local_playwright_fetch(params: dict, playwright_url: Optional[str] = None) -> Any:
    """
    Fetch Google Flights data using Playwright.
    
    Args:
        params: Query parameters for the Google Flights URL
        playwright_url: WebSocket endpoint (ws:// or wss://) for remote Playwright instance.
                       If None, uses local Chromium browser.
    
    Returns:
        DummyResponse object with fetched content
    """
    url = "https://www.google.com/travel/flights?" + "&".join(f"{k}={v}" for k, v in params.items())
    body = asyncio.run(fetch_with_playwright(url, playwright_url))

    class DummyResponse:
        status_code = 200
        text = body
        text_markdown = body

    return DummyResponse
