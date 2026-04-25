# Belfast ↔ London Weekend Flight Scraper

This tool monitors flight prices for weekend trips between Belfast (BHD/BFS) and London (LHR/LGW/STN/LTN/LCY).

## Features
- Scrapes the next 26 weekends (6 months) of round-trip flights.
- Filters for Friday evening departures (≥17:00) and Sunday evening returns (≥17:00).
- Stores price history in a local SQLite database.
- Sends Telegram alerts for:
  - Absolute deals (Round-trip < £70).
  - Relative drops (≥15% or ≥20% cheaper than historical median for that weekend/route).

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (Note: `fast_flights` and its dependencies are required).

2. Set environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   export FLIGHT_DB_PATH="flights.db"
   ```

3. (Optional) Bootstrap the database with history (without sending alerts):
   ```bash
   python -m weekend_scraper.main backfill
   ```

## Usage

Run a single scrape and alert run:
```bash
python -m weekend_scraper.main scrape-once
```

### Scheduling
It is recommended to run this via cron every 6 hours:
```cron
0 */6 * * * cd /path/to/project && /path/to/python -m weekend_scraper.main scrape-once >> scraper.log 2>&1
```

## Configuration
- `SCRAPE_HORIZON_WEEKENDS`: Default 26.
- `FLIGHT_DB_PATH`: Default `flights.db`.
- `TELEGRAM_BOT_TOKEN`: Required for alerts.
- `TELEGRAM_CHAT_ID`: Required for alerts.
