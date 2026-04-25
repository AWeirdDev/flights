import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional
from .models import PriceSample

class FlightStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_samples (
                    id              INTEGER PRIMARY KEY,
                    scraped_at      TEXT NOT NULL,
                    out_date        TEXT NOT NULL,
                    ret_date        TEXT NOT NULL,
                    from_airport    TEXT NOT NULL,
                    to_airport      TEXT NOT NULL,
                    price_gbp       INTEGER NOT NULL,
                    out_depart_hhmm TEXT,
                    ret_depart_hhmm TEXT,
                    airlines        TEXT,
                    raw             TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_weekend_route
                    ON price_samples (out_date, ret_date, from_airport, to_airport)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts_sent (
                    id              INTEGER PRIMARY KEY,
                    sent_at         TEXT NOT NULL,
                    sample_id       INTEGER NOT NULL REFERENCES price_samples(id),
                    rule            TEXT NOT NULL,
                    dedup_key       TEXT NOT NULL UNIQUE
                )
            """)

    def save_sample(self, sample: PriceSample) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO price_samples (
                    scraped_at, out_date, ret_date, from_airport, to_airport,
                    price_gbp, out_depart_hhmm, ret_depart_hhmm, airlines, raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sample.scraped_at.isoformat(),
                sample.out_date,
                sample.ret_date,
                sample.from_airport,
                sample.to_airport,
                sample.price_gbp,
                sample.out_depart_hhmm,
                sample.ret_depart_hhmm,
                json.dumps(sample.airlines),
                sample.raw
            ))
            sample.id = cursor.lastrowid
            return sample.id

    def get_history(self, out_date: str, ret_date: str, from_airport: str, to_airport: str) -> list[int]:
        """Returns historical prices in pennies for this weekend/route."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT price_gbp FROM price_samples
                WHERE out_date = ? AND ret_date = ? AND from_airport = ? AND to_airport = ?
                ORDER BY scraped_at DESC
            """, (out_date, ret_date, from_airport, to_airport))
            return [row[0] for row in cursor.fetchall()]

    def was_alert_sent(self, dedup_key: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT 1 FROM alerts_sent WHERE dedup_key = ?", (dedup_key,))
            return cursor.fetchone() is not None

    def record_alert(self, sample_id: int, rule: str, dedup_key: str):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO alerts_sent (sent_at, sample_id, rule, dedup_key)
                VALUES (?, ?, ?, ?)
            """, (datetime.now(timezone.utc).isoformat(), sample_id, rule, dedup_key))
