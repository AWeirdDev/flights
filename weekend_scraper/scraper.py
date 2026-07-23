from datetime import date, datetime, timezone
import json
from typing import Optional

from fast_flights import create_query, get_flights, FlightQuery, Passengers
from .models import PriceSample
from .routes import Route

import time
import random

def scrape_weekend_route(
    friday: date, 
    sunday: date, 
    route: Route,
    integration = None
) -> Optional[PriceSample]:
    """
    Scrapes Google Flights using one-way pairing (more reliable).
    Filters for outbound Fri >= 17:00 and inbound Sun >= 17:00.
    """
    def get_oneway(date_obj, src, dest):
        q = create_query(
            flights=[FlightQuery(date=date_obj.strftime("%Y-%m-%d"), from_airport=src, to_airport=dest)],
            trip="one-way", language="en-GB", currency="GBP"
        )
        # Retry logic
        for attempt in range(3):
            try:
                res = get_flights(q, integration=integration)
                if res: return res
            except Exception as e:
                print(f"    [ERROR] {src}->{dest} on {date_obj}: {e}")
            if attempt < 2: time.sleep(2)
        return []

    # 1. Get Outbound
    out_options = get_oneway(friday, route.from_airport, route.to_airport)
    # 2. Get Return
    ret_options = get_oneway(sunday, route.to_airport, route.from_airport)

    if not out_options or not ret_options:
        return None

    # 3. Filter and Pair
    best_pair = None # (out_f, ret_f, total_price)

    for out_f in out_options:
        out_time = out_f.flights[0].departure.time
        out_hour = out_time[0]
        out_min = out_time[1] if len(out_time) > 1 else 0

        # Skip flights fast_flights couldn't parse a departure time for.
        if out_hour is None: continue
        if out_hour < 17: continue # YOUR RULE: After 5pm

        for ret_f in ret_options:
            ret_time = ret_f.flights[0].departure.time
            ret_hour = ret_time[0]
            ret_min = ret_time[1] if len(ret_time) > 1 else 0

            if ret_hour is None: continue
            if ret_hour < 17: continue # YOUR RULE: After 5pm

            if out_min is None: out_min = 0
            if ret_min is None: ret_min = 0
            
            total_pennies = int((out_f.price + ret_f.price) * 100)
            
            if best_pair is None or total_pennies < best_pair[2]:
                best_pair = (out_f, ret_f, total_pennies, f"{out_hour:02d}:{out_min:02d}", f"{ret_hour:02d}:{ret_min:02d}")

    if not best_pair:
        return None

    out_f, ret_f, price, out_hhmm, ret_hhmm = best_pair
    
    return PriceSample(
        scraped_at=datetime.now(timezone.utc),
        out_date=friday.strftime("%Y-%m-%d"),
        ret_date=sunday.strftime("%Y-%m-%d"),
        from_airport=route.from_airport,
        to_airport=route.to_airport,
        price_gbp=price,
        out_depart_hhmm=out_hhmm,
        ret_depart_hhmm=ret_hhmm,
        airlines=list(set(out_f.airlines + ret_f.airlines)),
        raw=""
    )
