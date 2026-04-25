import os
import tempfile
from datetime import datetime, timezone
from weekend_scraper.store import FlightStore
from weekend_scraper.models import PriceSample

def test_store_save_and_get_history():
    with tempfile.NamedTemporaryFile() as tmp:
        db_path = tmp.name
        store = FlightStore(db_path)
        
        sample = PriceSample(
            scraped_at=datetime.now(timezone.utc),
            out_date="2026-05-01",
            ret_date="2026-05-03",
            from_airport="BHD",
            to_airport="LHR",
            price_gbp=6500,
            out_depart_hhmm="18:00",
            ret_depart_hhmm="19:00",
            airlines=["BA"]
        )
        
        sample_id = store.save_sample(sample)
        assert sample_id is not None
        
        history = store.get_history("2026-05-01", "2026-05-03", "BHD", "LHR")
        assert history == [6500]

def test_store_alerts():
    with tempfile.NamedTemporaryFile() as tmp:
        db_path = tmp.name
        store = FlightStore(db_path)
        
        dedup_key = "absolute:2026-05-01:2026-05-03:BHD:LHR:65"
        assert not store.was_alert_sent(dedup_key)
        
        store.record_alert(1, "absolute", dedup_key)
        assert store.was_alert_sent(dedup_key)
