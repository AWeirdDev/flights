# original by @Manouchehri
# pr: #64

from typing import Optional, Union
from primp import Client

from .base import Integration, get_env
from ..querying import Query
from ..fetcher import URL

DEFAULT_API_URL = "https://api.brightdata.com/request"
DEFAULT_DATA_SERP_ZONE = "serp_api1"


class BrightData(Integration):
    __slots__ = ("api_url", "zone")

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
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

    def fetch_html(self, q: Union[Query, str], /) -> str:
        if isinstance(q, str):
            res = self.client.post(
                self.api_url, json={"url": URL + "?q=" + q, "zone": self.zone}
            )
        else:
            res = self.client.post(
                self.api_url, json={"url": q.url(), "zone": self.zone}
            )

        return res.text
