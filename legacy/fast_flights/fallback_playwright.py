from typing import Any

from .primp import Client

CODE = """\
import asyncio
import sys
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("%s")
        locator = page.locator('.eQ35Ce')
        await locator.wait_for()
        body = await page.evaluate(
            \"\"\"() => {
                return document.querySelector('[role="main"]').innerHTML
            }\"\"\"
        )
        await browser.close()
    sys.stdout.write(body)

asyncio.run(main())
"""


def fallback_playwright_fetch(params: dict) -> Any:
    client = Client(impersonate="chrome_100", verify=False)

    res = client.post(
        "https://try.playwright.tech/service/control/run",
        json={
            "code": CODE
            % (
                "https://www.google.com/travel/flights"
                + "?"
                + "&".join(f"{k}={v}" for k, v in params.items())
            ),
            "language": "python",
        },
    )
    assert res.status_code == 200, f"{res.status_code} Result: {res.text_markdown}"
    import json

    class DummyResponse:
        status_code = 200
        text = json.loads(res.text)["output"]
        text_markdown = text

    return DummyResponse
