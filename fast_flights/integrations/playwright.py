from typing import Any

from ..fetch_result import FetchResult
from ..querying import Query
from .base import Integration

XHR_MARKER = "FlightsFrontendService/GetShoppingResults"


class Playwright(Integration):
    """Local Chromium integration that captures Google Flights shopping XHRs."""

    def fetch_html(self, q: Query | str, /) -> FetchResult:
        from playwright.sync_api import sync_playwright

        url = q.url() if isinstance(q, Query) else "https://www.google.com/travel/flights?q=" + q
        response_objects: list[Any] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/145.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """)

            def on_response(response: Any) -> None:
                if XHR_MARKER in response.url:
                    response_objects.append(response)

            page.on("response", on_response)
            try:
                page.goto(
                    "https://www.google.com/travel/flights",
                    timeout=25_000,
                    wait_until="domcontentloaded",
                )
                page.wait_for_timeout(1_000)
            except Exception:
                pass

            page.goto(url, timeout=25_000, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=12_000)
            except Exception:
                pass
            page.wait_for_timeout(2_000)

            xhr_bodies: list[bytes] = []
            for response in response_objects:
                try:
                    xhr_bodies.append(response.body())
                except Exception:
                    pass

            html = page.content()
            browser.close()

        return FetchResult(html=html, xhr_bodies=xhr_bodies, url=url)
