import os
import json
import urllib.request
from typing import List
from .alerter import Alert

from datetime import datetime

def format_telegram_message(alerts: List[Alert]) -> str:
    """
    Formats a list of alerts into a chronological, monthly-grouped Telegram message.
    """
    if not alerts:
        return ""
        
    # Group by unique flight pair
    unique_deals = {}
    for alert in alerts:
        # A deal is defined by its dates, route, and price
        s = alert.sample
        key = (s.out_date, s.ret_date, s.from_airport, s.to_airport, s.price_gbp)
        
        if key not in unique_deals:
            unique_deals[key] = {
                "sample": s,
                "is_deal": False,
                "drop_info": None
            }
        
        if alert.rule == "absolute":
            unique_deals[key]["is_deal"] = True
        if alert.rule in ("drop_15", "drop_20"):
            unique_deals[key]["drop_info"] = f"-{int(alert.drop_percent * 100)}% vs £{alert.median_price//100} median"

    # Sort deals: Month first, then Priority (LHR/LGW), then price
    def sort_key(deal):
        s = deal["sample"]
        is_priority = s.to_airport in ("LHR", "LGW")
        return (s.out_date, not is_priority, s.price_gbp)

    sorted_deals = sorted(unique_deals.values(), key=sort_key)
    
    lines = ["<b>✈️ Belfast ↔ London Deals Found</b>\n<i>Prices are total for both one-way legs combined.</i>\n"]
    
    current_month = ""
    
    for deal in sorted_deals:
        s = deal["sample"]
        is_priority = s.to_airport in ("LHR", "LGW")
        
        # Add monthly header
        deal_date = datetime.strptime(s.out_date, "%Y-%m-%d")
        month_str = deal_date.strftime("%B %Y")
        if month_str != current_month:
            current_month = month_str
            lines.append(f"\n─── <b>{month_str.upper()}</b> ───")
        
        price_total = s.price_gbp // 100
        
        # Build leg info
        priority_star = "⭐ " if is_priority else ""
        out_info = f"🛫 {s.from_airport}→{s.to_airport} (Fri {s.out_date} @ {s.out_depart_hhmm})"
        ret_info = f"🛬 {s.to_airport}→{s.from_airport} (Sun {s.ret_date} @ {s.ret_depart_hhmm})"
        
        deal_label = "🔥 DEAL" if deal["is_deal"] else "📉 DROP"
        if deal["drop_info"]:
            deal_label += f" ({deal['drop_info']})"
            
        lines.append(f"{priority_star}<b>£{price_total}</b>  [{deal_label}]")
        lines.append(f"   {out_info}")
        lines.append(f"   {ret_info}\n")
        
    return "\n".join(lines)

def send_telegram_alert(token: str, chat_id: str, message: str):
    """
    Sends a message to a Telegram chat.
    """
    if not message:
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML" # Optional, but good for bolding etc if we want
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req) as response:
        return response.read()
