from typing import Optional, Union
from primp import Client

from .querying import Query, StrQuery, StrQueryHolder, str_query
from .parser import parse

URL = "https://www.google.com/travel/flights"


def get_flights(
    q: Union[Query, StrQuery, StrQueryHolder, str], *, proxy: Optional[str] = None
):
    client = Client(
        impersonate="chrome_133",
        impersonate_os="macos",
        referer=True,
        proxy=proxy,
        cookie_store=True,
    )

    if isinstance(q, Query):
        params = q.params()

    elif isinstance(q, tuple):
        # StrQuery
        params = str_query(q).params()

    elif isinstance(q, StrQueryHolder):
        params = q.params()

    else:
        params = {"q": q}

    res = client.get(URL, params=params)
    return parse(res.text, source="js")
