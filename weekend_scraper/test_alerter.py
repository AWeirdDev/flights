from datetime import datetime, timezone
from weekend_scraper.alerter import get_alerts, Alert
from weekend_scraper.models import PriceSample

def test_get_alerts_absolute():
    sample = PriceSample(
        scraped_at=datetime.now(timezone.utc),
        out_date="2026-05-01", ret_date="2026-05-03",
        from_airport="BHD", to_airport="LHR",
        price_gbp=6900, out_depart_hhmm="18:00", ret_depart_hhmm="19:00",
        airlines=["BA"]
    )
    alerts = get_alerts(sample, [])
    assert len(alerts) == 1
    assert alerts[0].rule == "absolute"

    sample.price_gbp = 7000
    alerts = get_alerts(sample, [])
    assert len(alerts) == 0

def test_get_alerts_relative():
    history = [8000, 8200, 8500, 7900, 8100] # median is 8100
    sample = PriceSample(
        scraped_at=datetime.now(timezone.utc),
        out_date="2026-05-01", ret_date="2026-05-03",
        from_airport="BHD", to_airport="LHR",
        price_gbp=6800, # (8100-6800)/8100 = 1300/8100 = 16% drop
        out_depart_hhmm="18:00", ret_depart_hhmm="19:00",
        airlines=["BA"]
    )
    alerts = get_alerts(sample, history)
    assert len(alerts) == 2
    rules = {a.rule for a in alerts}
    assert "absolute" in rules
    assert "drop_15" in rules
    
    sample.price_gbp = 6400 # (8100-6400)/8100 = 1700/8100 = 21% drop
    alerts = get_alerts(sample, history)
    # Both absolute (6400 < 7000) and drop_20 should fire
    assert len(alerts) == 2
    rules = {a.rule for a in alerts}
    assert "absolute" in rules
    assert "drop_20" in rules

def test_get_alerts_absolute_european_threshold():
    sample = PriceSample(
        scraped_at=datetime.now(timezone.utc),
        out_date="2026-06-05", ret_date="2026-06-07",
        from_airport="BFS", to_airport="BCN",
        price_gbp=12900, out_depart_hhmm="18:00", ret_depart_hhmm="19:00",
        airlines=["VY"]
    )
    alerts = get_alerts(sample, [])
    assert len(alerts) == 1
    assert alerts[0].rule == "absolute"

    sample.price_gbp = 13000
    assert get_alerts(sample, []) == []

    for eu in ("CDG", "AMS", "AGP"):
        sample.to_airport = eu
        sample.price_gbp = 12500
        assert any(a.rule == "absolute" for a in get_alerts(sample, []))

def test_get_alerts_no_history():
    history = [8000, 8200, 8500, 7900] # only 4 samples
    sample = PriceSample(
        scraped_at=datetime.now(timezone.utc),
        out_date="2026-05-01", ret_date="2026-05-03",
        from_airport="BHD", to_airport="LHR",
        price_gbp=6000, # 25% drop but not enough history
        out_depart_hhmm="18:00", ret_depart_hhmm="19:00",
        airlines=["BA"]
    )
    alerts = get_alerts(sample, history)
    assert len(alerts) == 1
    assert alerts[0].rule == "absolute"
    assert all(a.rule != "drop_20" for a in alerts)
