import os
from unittest.mock import patch, MagicMock
from datetime import date
from weekend_scraper.main import main
from weekend_scraper.models import PriceSample


def _run_main(sample, argv_extra=None):
    argv_extra = argv_extra or []
    with patch("weekend_scraper.main.scrape_weekend_route") as mock_scrape, \
         patch("weekend_scraper.main.FlightStore") as mock_store_class, \
         patch("weekend_scraper.main.send_telegram_alerts") as mock_send, \
         patch("time.sleep", return_value=None):

        mock_store = MagicMock()
        mock_store_class.return_value = mock_store
        mock_store.get_history.return_value = []
        mock_scrape.return_value = sample

        with patch("sys.argv", ["main.py", "scrape-once", "--horizon", "1", *argv_extra]), \
             patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test", "TELEGRAM_CHAT_ID": "test"}):
            main()

        return mock_scrape, mock_store, mock_send


def test_main_scrapes_every_route_and_sends_four_segment_messages():
    sample = PriceSample(
        scraped_at=date.today(),
        out_date="2026-05-15", ret_date="2026-05-17",
        from_airport="BHD", to_airport="LHR",
        price_gbp=6500, out_depart_hhmm="19:05", ret_depart_hhmm="20:15",
        airlines=["BA"],
    )

    mock_scrape, mock_store, mock_send = _run_main(sample)

    # 2 origins * 9 destinations
    assert mock_scrape.call_count == 18
    assert mock_store.save_sample.call_count == 18
    # Sent once, with the full list of 4 segment messages
    assert mock_send.call_count == 1
    _, _, messages = mock_send.call_args.args
    assert len(messages) == 4


def test_main_does_not_gate_on_previously_sent_alerts():
    sample = PriceSample(
        scraped_at=date.today(),
        out_date="2026-05-15", ret_date="2026-05-17",
        from_airport="BHD", to_airport="LHR",
        price_gbp=6500, out_depart_hhmm="19:05", ret_depart_hhmm="20:15",
        airlines=["BA"],
    )

    _, mock_store, mock_send = _run_main(sample)

    # The digest shows all current deals; it must not consult the dedup table.
    mock_store.was_alert_sent.assert_not_called()
    _, _, messages = mock_send.call_args.args
    # Every scraped route was a qualifying LHR deal, so London message has deals.
    assert "£65" in messages[0]
