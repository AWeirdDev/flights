# original by @Manouchehri
# pr: #64

from primp import Client
from typing_extensions import Final, override

from ..fetcher import URL
from ..querying import Query
from .base import FetchIntegration, get_env

DEFAULT_API_URL = "https://api.brightdata.com/request"
DEFAULT_DATA_SERP_ZONE = "serp_api1"


class BrightData(FetchIntegration):
    """The [BrightData](https://brightdata.com) integration.

    Args:
        api_key (optional): The API key (or env variable `BRIGHT_DATA_API_KEY`).
        api_url (optional): The API URL (or env variable `BRIGHT_DATA_API_URL`).
        zone (optional): The data serp zone. Defaults to `serp_api1`.
    """

    __slots__: Final = ("api_url", "zone")

    api_url: str
    zone: str
    client: Client

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_url: str = DEFAULT_API_URL,
        zone: str = DEFAULT_DATA_SERP_ZONE,
    ):
        self.api_url = api_url or get_env("BRIGHT_DATA_API_URL")
        self.zone = zone
        self.client = Client(
            headers={
                "Authorization": "Bearer " + (api_key or get_env("BRIGHT_DATA_API_KEY"))
            }
        )

    @override
    def fetch_html(self, q: Query | str, /) -> str:
        # Bright Data's /request endpoint now requires an explicit "format"
        # field ("Request validation failed" / "\"format\" is required"
        # otherwise). Confirmed live 2026-08-30 against a real SERP API zone:
        # every request 400s without this, regardless of account/zone
        # configuration. "raw" matches what this integration actually needs,
        # since fetch_html() returns HTML text for the caller's parser to
        # read the embedded `ds:1` script tag from.
        if isinstance(q, str):
            res = self.client.post(
                self.api_url,
                json={"url": URL + "?q=" + q, "zone": self.zone, "format": "raw"},
            )
        else:
            res = self.client.post(
                self.api_url,
                json={"url": q.url(), "zone": self.zone, "format": "raw"},
            )

        return res.text
