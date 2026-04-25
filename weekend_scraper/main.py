import os
import time
import random
import argparse
from datetime import date
from typing import Optional

from .weekends import next_n_weekends
from .routes import get_routes
from .scraper import scrape_weekend_route
from .store import FlightStore
from .alerter import get_alerts
from .telegram import format_telegram_message, send_telegram_alert
from fast_flights.integrations.bright_data import BrightData

def main():
    parser = argparse.ArgumentParser(description="Belfast ↔ London Weekend Flight Scraper")
    parser.add_argument("command", choices=["scrape-once", "backfill"], help="Command to run")
    parser.add_argument("--horizon", type=int, default=int(os.getenv("SCRAPE_HORIZON_WEEKENDS", "26")), help="Number of weekends to scrape")
    parser.add_argument("--db", default=os.getenv("FLIGHT_DB_PATH", "flights.db"), help="Path to SQLite DB")
    
    args = parser.parse_args()
    
    store = FlightStore(args.db)
    today = date.today()
    weekends = next_n_weekends(today, n=args.horizon)
    routes = get_routes()
    
    integration = None
    if os.getenv("BRIGHT_DATA_API_KEY"):
        integration = BrightData()
        print("Using Bright Data integration.")
    
    all_alerts = []
    
    print(f"Starting {args.command} for {len(weekends)} weekends and {len(routes)} routes...")
    
    for friday, sunday in weekends:
        for route in routes:
            print(f"Scraping {route.from_airport} ↔ {route.to_airport} for {friday} - {sunday}...")
            
            # 1. Scrape
            sample = scrape_weekend_route(friday, sunday, route, integration=integration)
            
            if sample:
                print(f"  [FOUND] {sample.from_airport}→{sample.to_airport} at £{sample.price_gbp/100}")
                # 2. Get history
                history = store.get_history(sample.out_date, sample.ret_date, sample.from_airport, sample.to_airport)
                
                # 3. Save sample
                store.save_sample(sample)
                
                # 4. Alert if not backfill
                if args.command == "scrape-once":
                    alerts = get_alerts(sample, history)
                    for alert in alerts:
                        if not store.was_alert_sent(alert.dedup_key):
                            all_alerts.append(alert)
                            store.record_alert(sample.id, alert.rule, alert.dedup_key)
            
            # Be polite to Google
            time.sleep(random.uniform(1.0, 3.0))
            
    if all_alerts:
        message = format_telegram_message(all_alerts)
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if token and chat_id:
            print(f"Sending {len(all_alerts)} alerts to Telegram...")
            send_telegram_alert(token, chat_id, message)
        else:
            print("Telegram credentials missing, printing message instead:")
            print(message)
    else:
        print("No new alerts.")

if __name__ == "__main__":
    main()
