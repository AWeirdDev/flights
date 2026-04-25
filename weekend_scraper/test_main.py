import os
from unittest.mock import patch, MagicMock
from datetime import date
from weekend_scraper.main import main
from weekend_scraper.models import PriceSample
from weekend_scraper.routes import Route

def test_main_scrape_once():
    # Mocking dependencies
    with patch("weekend_scraper.main.scrape_weekend_route") as mock_scrape, \
         patch("weekend_scraper.main.FlightStore") as mock_store_class, \
         patch("weekend_scraper.main.send_telegram_alert") as mock_send, \
         patch("time.sleep", return_value=None):
        
        # Setup mocks
        mock_store = MagicMock()
        mock_store_class.return_value = mock_store
        mock_store.get_history.return_value = []
        mock_store.was_alert_sent.return_value = False
        
        sample = PriceSample(
            scraped_at=date.today(),
            out_date="2026-05-15", ret_date="2026-05-17",
            from_airport="BHD", to_airport="LHR",
            price_gbp=6500, out_depart_hhmm="19:05", ret_depart_hhmm="20:15",
            airlines=["BA"]
        )
        mock_scrape.return_value = sample
        
        # Run with small horizon to keep it fast
        with patch("sys.argv", ["main.py", "scrape-once", "--horizon", "1"]), \
             patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test", "TELEGRAM_CHAT_ID": "test"}):
            main()
            
        # Verify
        assert mock_scrape.call_count == 10 # 2 origins * 5 destinations
        assert mock_store.save_sample.call_count == 10
        assert mock_send.call_count == 1
