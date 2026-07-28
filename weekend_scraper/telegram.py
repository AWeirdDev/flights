import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import List

from .alerter import Alert


@dataclass(frozen=True)
class Segment:
    emoji: str
    name: str
    airports: tuple[str, ...]
    cap_label: str


# Order here is the order messages are sent in.
SEGMENTS: list[Segment] = [
    Segment("✈️", "Belfast ↔ London", ("LHR", "LGW", "STN", "LTN", "LCY"), "£100"),
    Segment("🇳🇱", "Belfast ↔ Amsterdam", ("AMS",), "£130"),
    Segment("🇫🇷", "Belfast ↔ Paris", ("CDG",), "£130"),
    Segment("🇪🇸", "Belfast ↔ Spain (Barcelona & Málaga)", ("BCN", "AGP"), "£130"),
]

PRIORITY_AIRPORTS = ("LHR", "LGW")


def _dedupe_deals(alerts: List[Alert]) -> dict:
    """Collapse the alerts for a single flight pair into one deal entry."""
    unique_deals: dict = {}
    for alert in alerts:
        s = alert.sample
        key = (s.out_date, s.ret_date, s.from_airport, s.to_airport, s.price_gbp)
        if key not in unique_deals:
            unique_deals[key] = {"sample": s, "is_deal": False, "drop_info": None}
        if alert.rule == "absolute":
            unique_deals[key]["is_deal"] = True
        if alert.rule in ("drop_15", "drop_20"):
            unique_deals[key]["drop_info"] = (
                f"-{int(alert.drop_percent * 100)}% vs £{alert.median_price // 100} median"
            )
    return unique_deals


def _sort_key(deal: dict):
    s = deal["sample"]
    is_priority = s.to_airport in PRIORITY_AIRPORTS
    return (s.out_date, not is_priority, s.price_gbp)


def _format_segment(segment: Segment, alerts: List[Alert]) -> str:
    header = f"<b>{segment.emoji} {segment.name}</b>"

    if not alerts:
        return f"{header}\n\nNo deals under {segment.cap_label} this run."

    sorted_deals = sorted(_dedupe_deals(alerts).values(), key=_sort_key)

    lines = [header, "<i>Prices are total for both one-way legs combined.</i>"]
    current_month = ""

    for deal in sorted_deals:
        s = deal["sample"]
        is_priority = s.to_airport in PRIORITY_AIRPORTS

        month_str = datetime.strptime(s.out_date, "%Y-%m-%d").strftime("%B %Y")
        if month_str != current_month:
            current_month = month_str
            lines.append(f"\n─── <b>{month_str.upper()}</b> ───")

        price_total = s.price_gbp // 100
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


def format_segment_messages(alerts: List[Alert]) -> List[str]:
    """
    Split alerts into one Telegram message per destination segment.

    Always returns exactly len(SEGMENTS) messages, in segment order. A segment
    with no qualifying deals renders a short "No deals" placeholder.
    """
    messages = []
    for segment in SEGMENTS:
        seg_alerts = [a for a in alerts if a.sample.to_airport in segment.airports]
        messages.append(_format_segment(segment, seg_alerts))
    return messages


def send_telegram_alert(token: str, chat_id: str, message: str):
    """Sends a single message to a Telegram chat."""
    if not message:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as response:
        return response.read()


def send_telegram_alerts(token: str, chat_id: str, messages: List[str]):
    """Sends each segment message as its own Telegram message."""
    for index, message in enumerate(messages):
        send_telegram_alert(token, chat_id, message)
        if index < len(messages) - 1:
            time.sleep(0.5)
