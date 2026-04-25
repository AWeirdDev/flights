from datetime import datetime, timezone
from weekend_scraper.telegram import format_telegram_message
from weekend_scraper.alerter import Alert
from weekend_scraper.models import PriceSample

def test_format_telegram_message():
    sample1 = PriceSample(
        scraped_at=datetime.now(timezone.utc),
        out_date="2026-05-15", ret_date="2026-05-17",
        from_airport="BHD", to_airport="LHR",
        price_gbp=5900, out_depart_hhmm="19:05", ret_depart_hhmm="20:15",
        airlines=["BA"]
    )
    alert1 = Alert(sample=sample1, rule="absolute")
    alert2 = Alert(sample=sample1, rule="drop_20", median_price=8100, drop_percent=0.27)
    
    sample2 = PriceSample(
        scraped_at=datetime.now(timezone.utc),
        out_date="2026-05-22", ret_date="2026-05-24",
        from_airport="BFS", to_airport="STN",
        price_gbp=6400, out_depart_hhmm="21:40", ret_depart_hhmm="18:55",
        airlines=["Ryanair"]
    )
    alert3 = Alert(sample=sample2, rule="absolute")
    
    message = format_telegram_message([alert1, alert2, alert3])
    
    assert "Belfast ↔ London — 2 deals" in message
    assert "£59  BHD→LHR" in message
    assert "Fri 2026-05-15 19:05 / Sun 2026-05-17 20:15" in message
    assert "absolute, drop_20, -27% vs £81 median" in message
    assert "£64  BFS→STN" in message
