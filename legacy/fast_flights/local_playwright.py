from typing import Any
import asyncio
from playwright.async_api import async_playwright

async def fetch_with_playwright(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        if page.url.startswith("https://consent.google.com"):
            await page.click('text="Accept all"')
        locator = page.locator('.eQ35Ce')
        await locator.wait_for()
        body = await page.evaluate(
            "() => document.querySelector('[role=\"main\"]').innerHTML"
        )
        await browser.close()
    return body

def local_playwright_fetch(params: dict) -> Any:
    url = "https://www.google.com/travel/flights?" + "&".join(f"{k}={v}" for k, v in params.items())
    body = asyncio.run(fetch_with_playwright(url))

    class DummyResponse:
        status_code = 200
        text = body
        text_markdown = body

    return DummyResponse
