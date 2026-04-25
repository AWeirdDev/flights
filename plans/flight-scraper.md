# Belfast ↔ London Weekend Flight Scraper

**Status:** Plan only — no code yet. Awaiting approval.
**Owner:** Aaron
**Created:** 2026-04-24

## 1. Goal

Every time the script runs, pull Google Flights prices for **round-trip Belfast ↔ London weekend getaways** (Fri evening out, Sun evening back), for the **next 26 weekends (~6 months)**, store them in a local price history DB, and push a Telegram alert whenever a deal meets one of our rules.

Two alert rules:
1. **Absolute cap** — any round-trip total **< £70**.
2. **Relative drop** — price is **≥15% cheaper** than the historical median for that same weekend / route pair (and a louder alert at **≥20%**).

The script should be idempotent, safe to run on a cron, and survive Google's occasional response changes. It should *not* require any Google Flights UI automation — we drive the `fast_flights` protobuf URL builder that already lives in this repo.

## 2. Non-goals

- No booking, no payment, no account linking.
- No multi-passenger / non-economy support in v1 (adult, economy, 1 bag — hardcoded).
- No non-weekend trips (Fri→Sun is the only shape).
- No real-time "watch this flight" pushes — we poll on a schedule.
- No web UI. CLI + Telegram only.

## 3. Constraints & assumptions

| # | Constraint | Source |
|---|---|---|
| C1 | Depart **Friday ≥ 17:00** local | User |
| C2 | Return **Sunday ≥ 17:00** local | User |
| C3 | `GBP` currency, `en-GB` language — never EUR/USD | Prior bug |
| C4 | Belfast origins: **BHD** (City) and **BFS** (International) — scrape both | User (slight preference for BHD) |
| C5 | London destinations: **LHR, LGW, STN, LTN, LCY** — scrape all five | Implied — Belfast serves different Londons from different carriers |
| C6 | Horizon: **next 26 weekends** from run date | User ("6 months") |
| C7 | Absolute alert threshold: **£70** round-trip total | User |
| C8 | Relative alert thresholds: **15%** (info), **20%** (loud) vs historical median | User |
| C9 | Run on a schedule without human intervention | User |
| C10 | Must handle rate limiting / soft blocks from Google | Prior bug |

## 4. Why this approach will work where the previous attempt did not

The previous attempt drove the Google Flights **web UI** (typing into boxes, clicking dates). That failed because:

- Date / airport comboboxes rebuild on every keystroke.
- Currency silently flipped to EUR when the IP geolocated outside the UK.
- The results DOM is shadow-ified and diffs per-session.

`fast_flights` already avoids all three:

- It **builds the `tfs` query param directly** from protobuf (`Query.to_str()` → base64) — no typing, no boxes. See `fast_flights/querying.py:38`.
- It takes `currency` and `language` as **explicit query params** (`Query.params()`), so GBP / en-GB is pinned at the URL level. See `fast_flights/querying.py:52`.
- It parses the embedded JS data (`script.ds\:1`) rather than the rendered DOM, which is far more stable. See `fast_flights/parser.py:27`.

So the "one-shot" improvement is: **stop automating the UI, use the library's URL builder.** Everything else in this plan is wrapping / persistence / alerting around it.

## 5. High-level architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ weekend_gen  │──▶│   scraper    │──▶│ price_store  │──▶│  alerter     │
│ (26 Fri/Sun) │   │ (fast_flights│   │ (SQLite)     │   │ (£70 + %drop)│
│              │   │  per route)  │   │              │   │              │
└──────────────┘   └──────────────┘   └──────────────┘   └──────┬───────┘
                                                                │
                                                         ┌──────▼──────┐
                                                         │  telegram   │
                                                         │   sender    │
                                                         └─────────────┘
```

Five small, individually testable modules. Each is a pure function where possible; side effects (HTTP, DB, Telegram) are isolated behind thin adapters so tests don't hit the network.

### 5.1 Module responsibilities

- **`weekends.py`** — pure. `next_n_weekends(today, n=26) → [(friday_date, sunday_date), …]`.
- **`routes.py`** — pure. Enumerate the **10 origin/destination pairs** (2 Belfast × 5 London). Return a stable list.
- **`scraper.py`** — side-effecting. For each `(weekend, route)` build a round-trip `Query` via `fast_flights.create_query`, call `get_flights`, reduce to the **cheapest flight that satisfies C1+C2** (≥17:00 outbound Fri, ≥17:00 inbound Sun). Returns a normalised `PriceSample` dataclass.
- **`store.py`** — side-effecting. SQLite DB. Two tables (schema in §6).
- **`alerter.py`** — pure. Given the new samples + history, returns a list of `Alert` records (absolute + relative).
- **`telegram.py`** — side-effecting. Thin wrapper around `sendMessage`. Token + chat id from env.
- **`cli.py` / `main.py`** — glue. One subcommand: `scrape-once`. A second: `backfill` (same, but doesn't alert, just seeds history).

### 5.2 Dependencies (no new ones unless needed)

- `fast_flights` — already in this repo.
- `sqlite3` — stdlib.
- `httpx` or `requests` — for Telegram. `primp` is already pulled in by `fast_flights`; prefer stdlib `urllib` to avoid adding deps at all.
- `pytest` for tests.

## 6. Data model (SQLite)

```sql
CREATE TABLE price_samples (
    id              INTEGER PRIMARY KEY,
    scraped_at      TEXT NOT NULL,          -- ISO8601 UTC
    out_date        TEXT NOT NULL,          -- YYYY-MM-DD (Friday)
    ret_date        TEXT NOT NULL,          -- YYYY-MM-DD (Sunday)
    from_airport    TEXT NOT NULL,          -- BHD | BFS
    to_airport      TEXT NOT NULL,          -- LHR | LGW | STN | LTN | LCY
    price_gbp       INTEGER NOT NULL,       -- total round-trip, pennies
    out_depart_hhmm TEXT,                   -- '17:45'
    ret_depart_hhmm TEXT,
    airlines        TEXT,                   -- JSON array
    raw             TEXT                    -- full fast_flights payload for debugging
);

CREATE INDEX idx_weekend_route
    ON price_samples (out_date, ret_date, from_airport, to_airport);

CREATE TABLE alerts_sent (
    id              INTEGER PRIMARY KEY,
    sent_at         TEXT NOT NULL,
    sample_id       INTEGER NOT NULL REFERENCES price_samples(id),
    rule            TEXT NOT NULL,          -- 'absolute' | 'drop_15' | 'drop_20'
    dedup_key       TEXT NOT NULL UNIQUE    -- prevents re-alerting the same deal
);
```

**Dedup key** = `f"{rule}:{out_date}:{ret_date}:{from_airport}:{to_airport}:{price_bucket}"` where `price_bucket` is price rounded to nearest £5. That way a £63 flight doesn't re-alert when it becomes £62, but a genuine new low (say £55) does.

## 7. Cheap-deal logic

```
for each PriceSample just scraped:
    history = all prior samples for same (out_date, ret_date, from_airport, to_airport)
    if price < 7000 (pennies):              → alert rule="absolute"
    if len(history) >= 5:                   # need a meaningful baseline
        median = median(history.price_gbp)
        drop = (median - price) / median
        if drop >= 0.20:                    → alert rule="drop_20"
        elif drop >= 0.15:                  → alert rule="drop_15"
```

Notes:

- Baseline is **per-weekend × per-route**, not global. A £90 STN flight is not "a drop" just because a £60 LHR flight existed for a different weekend.
- Until a weekend has ≥5 historical samples, only the absolute rule fires. This prevents spurious "drop" alerts from a one-sample baseline.
- We **do not dedupe across rules** — a flight can fire both "absolute" and "drop_20" on the same scrape. Aaron sees one merged Telegram message (see §8).

## 8. Telegram message format

One message per scrape run, grouped, sorted by price ascending. Nothing if zero alerts.

```
✈️ Belfast ↔ London — 3 deals

£59  BHD→LHR  Fri 15 May 19:05  /  LHR→BHD  Sun 17 May 20:15   [abs, -27% vs £81 median]
£64  BFS→STN  Fri 22 May 21:40  /  STN→BFS  Sun 24 May 18:55   [abs]
£68  BFS→LGW  Fri 19 Jun 17:55  /  LGW→BFS  Sun 21 Jun 19:40   [abs, -16% vs £81 median]

Booked? Reply /snooze <weekend> to suppress this pair for 30 days.
```

`/snooze` is a stretch goal — not v1.

## 9. Scheduling

- v1: **cron-driven**, not a long-running daemon. A single script invocation scrapes all 26 × 10 = 260 queries, writes samples, sends at most one Telegram message, exits.
- Suggested cadence: **every 6 hours**. That's 4 runs/day × 260 queries = 1,040 Google Flights hits/day. Well below anything Google would care about — but we add a 1–3s jitter between queries to be polite.
- Future: switch to an event loop and longpoll Telegram for `/snooze` etc.

**Why not on-demand only?** The whole point of the historical bank is to catch drops *the moment they happen*. On-demand can't do that.

## 10. Handling Google pushback

`fast_flights` uses `primp` with Chrome 145 macOS impersonation — usually enough. But two fallbacks:

1. **Retry with backoff** on empty `MetaList` or HTTP ≠ 200. 3 attempts, exponential 5s → 30s → 2m.
2. **Bright Data integration already exists** in `fast_flights/integrations/bright_data.py`. If `BRIGHT_DATA_API_KEY` is set in env, use it as `integration=BrightData()`. Keeps costs zero while dev, enables a paid escape hatch later.

We log every empty-result pair so we can see if one route is systematically being blocked and switch just that route to Bright Data.

## 11. Configuration

All via env vars (12-factor, no config file):

| Env | Required | Purpose |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes | Bot auth |
| `TELEGRAM_CHAT_ID` | yes | Where to send |
| `FLIGHT_DB_PATH` | no (default `./flights.db`) | SQLite location |
| `BRIGHT_DATA_API_KEY` | no | Only if we fall back |
| `SCRAPE_HORIZON_WEEKENDS` | no (default `26`) | Override 6-month horizon |
| `ABS_THRESHOLD_GBP` | no (default `70`) | Override cap |

## 12. Previous-attempt pitfalls — explicit re-check

| Prior pain | Mitigation in this plan |
|---|---|
| UI box typing flaky | We don't touch the UI. `tfs` URL param only. §4 |
| Prices came back in EUR | Pinned `currency="GBP"` at URL level. §6 / querying.py:52 |
| Date picker rejected YYYY-MM-DD | Not used — we pass date strings into protobuf. `FlightQuery.date` is ISO. querying.py:62 |
| Flaky HTML parsing | We use the embedded JS payload parser already in `fast_flights/parser.py`, which the maintainer keeps current. |
| Empty results silently "succeed" | Retries + Bright Data fallback + log-every-empty-result so we *see* it. §10 |
| Alert spam | Dedup table with £5 bucketing. §6 |
| No idea if a price is actually a deal | Per-weekend-per-route historical median w/ ≥5-sample gate. §7 |

## 13. Incremental delivery (TDD)

Each bullet is one red→green→refactor cycle with a commit gate. No step should take more than an hour.

1. **Weekend generator** (pure). Test: given `today=2026-04-24` and `n=3`, returns `[(2026-04-24, 2026-04-26), (2026-05-01, 2026-05-03), (2026-05-08, 2026-05-10)]`. Handles "today is already a Friday" correctly.
2. **Route enumeration** (pure). Test: returns the 10 known (BHD/BFS × LHR/LGW/STN/LTN/LCY) pairs, stable order.
3. **Scraper — happy path**, mocked. Test: given a fake `get_flights` returning two candidates, picks the one whose outbound is ≥17:00 Fri and return is ≥17:00 Sun, at the lowest price.
4. **Scraper — time filter**. Test: if all candidates depart before 17:00, returns None (not the cheapest overall — that would violate C1).
5. **Scraper — real call, one route, one weekend** (integration, marked `@pytest.mark.net`). Smoke test. Verifies GBP comes back GBP.
6. **Store** schema + insert + query-by-weekend+route. Tests hit `:memory:` SQLite.
7. **Alerter — absolute rule**. Test: £69 → alert. £70 → no alert. £71 → no alert.
8. **Alerter — relative rule**. Test: median of `[80, 82, 85, 79, 81]` is 81; new sample of £68 → drop ~16% → `drop_15`; £64 → ~21% → `drop_20`; fewer than 5 history samples → never fires relative.
9. **Alerter — dedup**. Test: same alert key twice → second one suppressed.
10. **Telegram sender**. Test: formats the §8 message correctly; HTTP call mocked. Separately, a manual one-off to prove the token works.
11. **Glue / main**. Test: end-to-end with mocked scraper — reads 3 weekends × 2 routes, stores, alerts, sends once.
12. **Cron wiring + README**. Cron line, env var list, "how to bootstrap the DB" (run `backfill` once with alerts suppressed so median isn't built on noise).

Rough effort: ~1 dev-day for steps 1–10, half-day for 11–12.

## 14. Open questions for Aaron before I start

1. **Bag policy.** £70 cap — is that hand-luggage only, or including a 23kg hold bag? Google Flights shows hand-luggage price by default; Ryanair charges extra for a bag and Aer Lingus doesn't. This changes which deals matter. **Default assumption: hand-luggage only.**
2. **"After 17:00" — is this depart-time or arrive-time?** I've assumed **depart-time** both directions (i.e. wheels-up ≥ 17:00 Fri from Belfast, wheels-up ≥ 17:00 Sun from London). Confirm?
3. **Preference tiebreak.** If BHD and BFS are within £X of each other, how much is the BHD preference worth? I propose: surface both in the alert if BHD is within £15 of the cheaper BFS; otherwise just the cheapest. OK?
4. **Telegram bot** — do you already have one, or do I need to create one via @BotFather and hand you the setup steps?
5. **Where will this run?** Codespaces will sleep, so cron-in-Codespaces is not reliable. A tiny always-on host (fly.io, a $4 VPS, a Raspberry Pi, GitHub Actions scheduled workflow) is needed. GitHub Actions `schedule:` every 6h is free and adequate — shall we go with that?
6. **Seed data.** Before the relative-drop rule can fire, every weekend needs ≥5 samples. That's ~30h of runtime at 6h cadence (5 × 6). Fine for absolute-only alerts in the meantime?

Answers to any of these will change the plan — particularly Q5, which changes §9 entirely.
