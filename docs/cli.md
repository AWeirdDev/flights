# flights-cli

`flights-cli` is the command-line interface for the `fast-flights` library.

# 🚀 Quick start

```bash
pip install git+https://github.com/swiftlysingh/flights-cli

flights-cli --round \
  --segment "date=2026-01-01 from=DEL to=SFO" \
  --segment "date=2026-01-10 from=SFO to=DEL" \
  --class economy --max-stops 1 --fetch-mode fallback --best-only
```

# 📦 Installation

Install the CLI alongside the Python package:

```bash
pip install git+https://github.com/swiftlysingh/flights-cli
```

This installs the `flights-cli` executable and exposes the module entry point so you can run it directly as well:

```bash
python -m fast_flights.cli --help
```

> Refer to the [filters documentation](filters.md) to take control over detailed options for flights with `flights-cli` and the [fallbacks documentation](fallbacks.md) for additional fetching strategies.

# 🧭 Commands

## `flights-cli`

### Options Overview

| Option | Description | Default |
| --- | --- | --- |
| `--trip {one-way,round-trip,multi-city}` | Explicit trip type. Overrides shortcut flags. | Automatically inferred from segments |
| `--one` | Shortcut for `--trip one-way` | — |
| `--round` | Shortcut for `--trip round-trip` | — |
| `--multi` | Shortcut for `--trip multi-city` | — |
| `--segment "date=YYYY-MM-DD from=AAA to=BBB [max_stops=N] [airlines=AA,BB]"` | Flight segment definition. Repeat for multiple segments. | None (required) |
| `--max-stops MAX_STOPS` | Maximum stops applied globally. | None |
| `--class {economy,premium-economy,business,first}` | Choose cabin class. | `economy` |
| `--fetch-mode {common,fallback,force-fallback,local,bright-data}` | Select backend strategy. See [fallbacks](fallbacks.md). | `common` |
| `--data-source {html,js}` | Switch between HTML parsing and decoded JS data. | `html` |
| `-a/--adults` | Number of adult passengers. | `1` |
| `-c/--children` | Number of children passengers. | `0` |
| `--infants-in-seat` | Number of infants in seats. | `0` |
| `--infants-on-lap` | Number of infants on lap. Must not exceed adults. | `0` |
| `--best-only` | Return only the best flight(s). Maps to `is_best`. | `False` |
| `--json` | Output structured JSON. | `False` |
| `--pretty` | Format JSON with indentation. | `False` |

### Segment format

Segments map to [`FlightData`](filters.md#flightdata) objects. Pass at least one `--segment` option to build the request. For round trips, specify two segments. For multi-city itineraries, add more segments.

```bash
flights-cli --segment "date=2026-06-01 from=LHR to=JFK max_stops=0"
```

Segments accept the following keys:

| Key | Required | Description |
| --- | --- | --- |
| `date` | ✅ | Departure date (YYYY-MM-DD). |
| `from` / `from_airport` | ✅ | Origin airport IATA code. |
| `to` / `to_airport` | ✅ | Destination airport IATA code. |
| `max_stops` | Optional | Maximum stops for the segment. Overrides global `--max-stops`. |
| `airlines` | Optional | Comma-separated airline codes (`AA,DL,...`) or alliances (`SKYTEAM`). |

Wrap the segment expression in quotes so the shell treats it as one value. Combine multiple `--segment` flags in the order that the legs should be flown.

### Passenger details

Passengers are captured by the `fast_flights.Passengers` class. CLI options map directly to its constructor:

```bash
flights-cli --segment "date=2026-08-05 from=BOS to=LAX" \
  -a 2 -c 1 --infants-in-seat 1
```

The CLI enforces the same validations: total passengers ≤ 9 and adult coverage for infants on lap.

### Trip type shortcuts

Use either the main `--trip` flag or the dedicated shortcuts:

```bash
flights-cli --round --segment "date=2026-01-01 from=DEL to=SFO" --segment "date=2026-01-10 from=SFO to=DEL"

flights-cli --one --segment "date=2026-02-14 from=JFK to=CDG"
```

If you omit trip flags, the CLI infers `round-trip` for two segments, otherwise `one-way`.

### Seats and cabins

Select the cabin with `--class`:

```bash
flights-cli --segment "date=2026-04-01 from=SYD to=NRT" --class business
```

### Fetch strategy

`--fetch-mode` controls which scraper implementation runs under the hood:

* `common`: default direct HTTP fetch.
* `fallback`: try direct fetch, fall back to Playwright Serverless if required.
* `force-fallback`: always use serverless Playwright.
* `local`: requires local Playwright setup; see [local mode](local.md).
* `bright-data`: uses the Bright Data proxy integration; see [fallbacks](fallbacks.md#bright-data).

### Data sources

`--data-source html` (default) returns high-level summaries matching `fast_flights.schema.Result`. `--data-source js` returns the raw decoded structure (`DecodedResult`) with detailed itinerary metadata, including layovers and aircraft. Both can be combined with `--json` output.

### Best-only responses

Use `--best-only` to get only the top recommendation. For HTML responses, this includes flights with the `is_best` flag. For JS responses, it surfaces only the `best` itineraries list.

```bash
flights-cli --segment "date=2026-09-09 from=SJC to=HNL" --best-only
```

### JSON output

Switch to machine-readable responses with `--json` and optionally format them with `--pretty`:

```bash
flights-cli --segment "date=2026-01-01 from=DEL to=SFO" --json --pretty
```

For `--best-only` JSON responses, the CLI filters the payload accordingly.

# 🧪 Examples

## One-way economy search

```bash
flights-cli --one \
  --segment "date=2026-02-05 from=JFK to=LHR" \
  --class economy -a 1
```

## Round-trip premium economy with fallback fetch

```bash
flights-cli --round \
  --segment "date=2026-06-15 from=LAX to=ICN" \
  --segment "date=2026-07-01 from=ICN to=LAX" \
  --class premium-economy --max-stops 1 --fetch-mode fallback
```

## Multi-city itinerary with different segments

```bash
flights-cli --multi \
  --segment "date=2026-03-01 from=SEA to=NRT" \
  --segment "date=2026-03-05 from=NRT to=HKG" \
  --segment "date=2026-03-10 from=HKG to=SEA"
```

## Force Playwright fallback

```bash
flights-cli --segment "date=2026-05-10 from=CDG to=BOM" --fetch-mode force-fallback
```

## Retrieve raw itineraries via JS decoder

```bash
flights-cli --segment "date=2026-02-01 from=SFO to=DEL" --data-source js --json --pretty
```

# 🔍 References

- [`filters.md`](filters.md): deeper control over segment definitions and airlines.
- [`airports.md`](airports.md): working with airport enums and helpers.
- [`fallbacks.md`](fallbacks.md): detail on fetch modes and infrastructure setup.
- [`local.md`](local.md): how to run the local Playwright variant.

For Python usage examples, see `example.py` and [`README.md`](../README.md).

