# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`fast-flights` is a Python library for scraping Google Flights data using Base64-encoded Protocol Buffers. It's a robust alternative to the discontinued Google Flights API that avoids the slowness of traditional browser automation by using Protobuf to construct queries and HTML parsing to extract results.

## Development Commands

### Running Tests

```bash
# Basic test
python test.py

# Test with Bright Data (requires BRIGHT_DATA_API_KEY env var)
./test_bright_data.py

# Test with JS data parsing
./test_jsdata.py
```

### Running Examples

```bash
# Basic example
python example.py --origin TPE --destination MYJ \
  --depart_date 2025-07-01 --return_date 2025-07-08 \
  --adults 2 --type economy --fetch_mode fallback

# Simple test file
python test.py
```

### Building the Package

```bash
# Build with flit
python -m flit build

# Install in development mode
pip install -e .

# Install with local Playwright support
pip install -e ".[local]"
```

### Documentation

```bash
# Build documentation (uses mkdocs)
mkdocs build

# Serve documentation locally
mkdocs serve
```

### Protocol Buffers

When modifying `.proto` files in `fast_flights/`:

```bash
# Compile protobuf files
protoc --python_out=. fast_flights/flights.proto
protoc --python_out=. fast_flights/cookies.proto
```

## Architecture

### Core Flow

1. **Filter Creation** (`filter.py`, `flights_impl.py`):
   - User provides flight parameters (dates, airports, passengers, etc.)
   - Protobuf message is constructed using `flights.proto` schema
   - Serialized to Base64 to create the `tfs` query parameter

2. **Data Fetching** (`core.py`):
   - Multiple fetch modes: `common`, `fallback`, `force-fallback`, `local`, `bright-data`
   - `common`: Uses `primp` HTTP client to scrape HTML directly
   - `fallback`: Falls back to Playwright serverless functions if scraping fails
   - `local`: Uses locally installed Playwright
   - `bright-data`: Uses Bright Data proxy service

3. **Parsing** (`core.py`, `decoder.py`):
   - Two data sources: `html` (default) and `js`
   - HTML parsing uses `selectolax` to extract flight data from DOM
   - JS parsing extracts structured data from `<script class="ds:1">` tags and decodes nested list structures

4. **Response Models** (`schema.py`):
   - Simple `Result` and `Flight` classes for HTML-parsed data
   - Complex `DecodedResult` with nested `Itinerary`, `Flight`, `Layover` for JS-parsed data

### Key Components

**Protobuf Schema** (`flights.proto`):
- Defines the structure for Google Flights query parameters
- Contains `FlightData`, `Airport`, `Seat`, `Trip`, `Passenger` enums
- `Info` message aggregates all filter parameters

**Filter System**:
- `TFSData` class wraps the Protobuf message
- `create_filter()` is the high-level API
- `get_flights()` combines filter creation and fetching in one call

**Decoder System** (`decoder.py`):
- Generic `Decoder` base class for decoding nested list data from JS
- `DecoderKey` specifies paths through nested lists using index arrays
- Separate decoders for `Flight`, `Layover`, `Itinerary`, `Result`

**Fallback Strategies**:
- `fallback_playwright.py`: Uses browserless.io Playwright service
- `local_playwright.py`: Uses locally installed Playwright
- `bright_data_fetch.py`: Uses Bright Data proxy API

**Generated Code**:
- `_generated_enum.py`: Large enum of airports with autocomplete support
- `*_pb2.py`: Auto-generated from `.proto` files (don't edit directly)

## Important Notes

### Fetch Modes

The library supports multiple strategies for robustness:

- Start with `fallback` mode (recommended) - tries direct scraping first, falls back to Playwright if needed
- Use `common` for speed when you know direct scraping works
- Use `force-fallback` to always use Playwright (useful for debugging or regions with cookie consent)
- Use `local` when developing/testing and want to avoid external Playwright services
- Use `bright-data` when you have a Bright Data subscription

### Data Sources

- `html` source: Fast, returns simple `Result` with basic flight info
- `js` source: More data (codeshares, layovers, detailed timing), returns rich `DecodedResult`

### Testing

When testing changes, be aware:
- Google Flights HTML structure can change without notice
- Always test with real flight searches, not mocked data
- Different routes may have different HTML structures (best flights, other flights, etc.)
- The `dangerously_allow_looping_last_item` parameter in `parse_response` handles edge cases in flight list iteration

### Protobuf Development

- Field numbers in `.proto` files must match Google's schema (discovered through reverse engineering)
- Don't change field numbers once set - they're part of the wire format
- After editing `.proto` files, regenerate `*_pb2.py` files
- The Protobuf schema is based on observing Google Flights URL parameters and reverse engineering

### Common Gotchas

- Passenger counts: Total must not exceed 9, and need 1 adult per infant on lap
- Round trips: Require 2+ `FlightData` objects in `flight_data` list
- Airport codes: Must be valid IATA codes (3 letters)
- Date format: Must be "YYYY-MM-DD"
- The `max_stops` parameter can be set per `FlightData` or globally via `create_filter`
