import base64
import time
import datetime as datetimelib

from .cookies_pb2 import SOCS, Information, Datetime  # type: ignore


class Cookies:
    def __init__(
        self,
        *,
        gws: str,
        locale: str,
        timestamp: int,
    ):
        self.gws = gws
        self.locale = locale
        self.timestamp = timestamp

    def pb(self) -> SOCS:  # type: ignore
        # Info
        info = Information()
        info.gws = self.gws
        info.locale = self.locale

        # Datetime
        datetime = Datetime()
        datetime.timestamp = self.timestamp

        # SOCS (main)
        socs = SOCS(info=info, datetime=datetime)
        return socs

    def to_string(self) -> bytes:
        return self.pb().SerializeToString()

    def as_b64(self) -> bytes:
        return base64.b64encode(self.to_string())

    def to_dict(self) -> dict:
        return {"CONSENT": "PENDING+987", "SOCS": self.as_b64().decode("utf-8")}

    @staticmethod
    def new(*, locale: str = "en") -> "Cookies":
        return Cookies(
            gws=f"gws_{datetimelib.datetime.now().strftime('%Y%m%d')}-0_RC2",
            locale=locale,
            timestamp=int(time.time()),
        )
