from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PriceSample:
    scraped_at: datetime
    out_date: str  # YYYY-MM-DD
    ret_date: str  # YYYY-MM-DD
    from_airport: str
    to_airport: str
    price_gbp: int  # in pennies
    out_depart_hhmm: str
    ret_depart_hhmm: str
    airlines: list[str]
    raw: str = ""
    id: Optional[int] = None
