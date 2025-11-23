from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from .core import get_flights
from .decoder import DecodedResult, Itinerary
from .flights_impl import FlightData, Passengers
from .schema import Flight, Result


def _parse_segment(segment: str) -> Dict[str, Any]:
    tokens = shlex.split(segment)
    if not tokens:
        raise ValueError("Segment cannot be empty")

    data: Dict[str, str] = {}
    key_map = {
        "date": "date",
        "from": "from_airport",
        "from_airport": "from_airport",
        "to": "to_airport",
        "to_airport": "to_airport",
        "max_stops": "max_stops",
        "airlines": "airlines",
    }

    for token in tokens:
        if "=" not in token:
            raise ValueError(
                f"Segment token '{token}' must follow key=value format. "
                "Enclose the whole segment in quotes."
            )
        raw_key, value = token.split("=", 1)
        key = raw_key.lower()
        if key not in key_map:
            raise ValueError(
                f"Unsupported segment key '{raw_key}'. Allowed keys: date, from, to, max_stops, airlines."
            )
        mapped_key = key_map[key]
        if mapped_key in data:
            raise ValueError(f"Duplicate '{raw_key}' in segment definition.")
        data[mapped_key] = value

    missing = {field for field in ("date", "from_airport", "to_airport") if field not in data}
    if missing:
        pretty_missing = ", ".join(sorted(missing))
        raise ValueError(f"Missing required keys in segment: {pretty_missing}")

    parsed: Dict[str, Any] = {
        "date": data["date"],
        "from_airport": data["from_airport"],
        "to_airport": data["to_airport"],
    }

    if "max_stops" in data and data["max_stops"]:
        try:
            parsed["max_stops"] = int(data["max_stops"])
        except ValueError as exc:
            raise ValueError("max_stops must be an integer") from exc

    if "airlines" in data and data["airlines"]:
        airlines = [code.strip().upper() for code in data["airlines"].split(",") if code.strip()]
        parsed["airlines"] = airlines if airlines else None

    return parsed


def _result_to_dict(result: Any) -> Dict[str, Any]:
    if isinstance(result, Result):
        return {
            "current_price": result.current_price,
            "flights": [asdict(flight) for flight in result.flights],
        }

    if isinstance(result, DecodedResult):
        def itinerary_to_dict(itinerary: Itinerary) -> Dict[str, Any]:
            data = asdict(itinerary)
            summary = itinerary.itinerary_summary
            data["itinerary_summary"] = {
                "flights": summary.flights,
                "price": summary.price,
                "currency": summary.currency,
            }
            return data

        return {
            "best": [itinerary_to_dict(itin) for itin in result.best],
            "other": [itinerary_to_dict(itin) for itin in result.other],
            "raw": result.raw,
        }

    raise TypeError("Unsupported result type returned from get_flights")


def _print_text_result(result: Any, *, best_only: bool) -> None:
    if isinstance(result, Result):
        flights: List[Flight] = result.flights
        if best_only:
            flights = [flight for flight in flights if flight.is_best] or flights[:1]
        print(f"Current price trend: {result.current_price}")
        if not flights:
            print("No flights returned.")
            return
        for index, flight in enumerate(flights, start=1):
            marker = "*" if flight.is_best else "-"
            price = flight.price or "N/A"
            delay = f" | Delay: {flight.delay}" if flight.delay else ""
            print(
                f"{marker} {index}. {flight.name} — {flight.departure} → {flight.arrival}"
                f" | Duration: {flight.duration} | Stops: {flight.stops} | Price: {price}{delay}"
            )
        return

    if isinstance(result, DecodedResult):
        itineraries: List[Itinerary] = result.best if best_only else result.best + result.other
        if best_only and not itineraries:
            print("No best itineraries returned.")
            return
        if not itineraries:
            print("No itineraries returned.")
            return
        print("Itineraries:")
        for index, itinerary in enumerate(itineraries, start=1):
            summary = itinerary.itinerary_summary
            airlines = ", ".join(itinerary.airline_names) or itinerary.airline_code
            print(
                f"- {index}. {itinerary.departure_airport} → {itinerary.arrival_airport}"
                f" on {airlines} | Travel time: {itinerary.travel_time} mins"
                f" | Price: {summary.price} {summary.currency}"
            )
        return

    raise TypeError("Unsupported result type returned from get_flights")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search Google Flights data via fast-flights",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    trip_group = parser.add_mutually_exclusive_group()
    trip_group.add_argument(
        "--trip",
        choices=["one-way", "round-trip", "multi-city"],
        help="Trip type. Overrides --one, --round, --multi if provided.",
    )
    trip_group.add_argument("--one", dest="trip_one", action="store_true", help="Shortcut for --trip one-way")
    trip_group.add_argument("--round", dest="trip_round", action="store_true", help="Shortcut for --trip round-trip")
    trip_group.add_argument("--multi", dest="trip_multi", action="store_true", help="Shortcut for --trip multi-city")

    parser.add_argument(
        "--segment",
        action="append",
        metavar='"date=YYYY-MM-DD from=AAA to=BBB [max_stops=N] [airlines=AA,BB]"',
        help="Define a flight segment. Provide the flag multiple times for multi-leg trips.",
    )

    parser.add_argument("--max-stops", type=int, default=None, help="Apply a maximum number of stops to the entire search.")

    parser.add_argument(
        "--class",
        dest="seat",
        choices=["economy", "premium-economy", "business", "first"],
        default="economy",
        help="Seat class (cabin).",
    )

    parser.add_argument("-a", "--adults", type=int, default=1, help="Number of adult passengers.")
    parser.add_argument("-c", "--children", type=int, default=0, help="Number of child passengers.")
    parser.add_argument("--infants-in-seat", type=int, default=0, help="Number of infants in their own seats.")
    parser.add_argument("--infants-on-lap", type=int, default=0, help="Number of infants on lap.")

    parser.add_argument(
        "--fetch-mode",
        choices=["common", "fallback", "force-fallback", "local", "bright-data"],
        default="common",
        help="Backend fetch strategy.",
    )

    parser.add_argument(
        "--data-source",
        choices=["html", "js"],
        default="html",
        help="Choose the data extraction strategy: HTML parser or JS decoded payload.",
    )

    parser.add_argument("--best-only", action="store_true", help="Return only the flights or itineraries marked as best.")
    parser.add_argument("--json", action="store_true", help="Print the response as JSON.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output when --json is supplied.")

    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Reserved for future use. Currently unused.",
    )

    return parser


def _resolve_trip(args: argparse.Namespace) -> str:
    if args.trip:
        return args.trip
    if args.trip_one:
        return "one-way"
    if args.trip_round:
        return "round-trip"
    if args.trip_multi:
        return "multi-city"
    # Default to round-trip if two segments, else one-way
    if args.segment and len(args.segment) == 2:
        return "round-trip"
    return "one-way"


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.segment:
        parser.error("At least one --segment must be provided.")

    segments: List[FlightData] = []
    for index, segment_spec in enumerate(args.segment, start=1):
        try:
            parsed_segment = _parse_segment(segment_spec)
        except ValueError as exc:
            parser.error(f"Invalid --segment #{index}: {exc}")

        segments.append(
            FlightData(
                date=parsed_segment["date"],
                from_airport=parsed_segment["from_airport"],
                to_airport=parsed_segment["to_airport"],
                max_stops=parsed_segment.get("max_stops"),
                airlines=parsed_segment.get("airlines"),
            )
        )

    try:
        passengers = Passengers(
            adults=args.adults,
            children=args.children,
            infants_in_seat=args.infants_in_seat,
            infants_on_lap=args.infants_on_lap,
        )
    except AssertionError as exc:
        parser.error(str(exc))

    trip = _resolve_trip(args)

    try:
        result = get_flights(
            flight_data=segments,
            trip=trip,
            passengers=passengers,
            seat=args.seat,
            fetch_mode=args.fetch_mode,
            max_stops=args.max_stops,
            data_source=args.data_source,
        )
    except Exception as exc:  # pragma: no cover - surface error message
        parser.exit(1, f"Failed to fetch flights: {exc}\n")

    if result is None:
        parser.exit(1, "No result returned from fast-flights.\n")

    if args.json:
        data = _result_to_dict(result)
        if args.best_only and isinstance(result, Result):
            data["flights"] = [flight for flight in data["flights"] if flight.get("is_best")]
        if args.best_only and isinstance(result, DecodedResult):
            data = {"best": data.get("best", [])}
        json.dump(data, sys.stdout, indent=2 if args.pretty else None)
        if args.pretty:
            sys.stdout.write("\n")
    else:
        _print_text_result(result, best_only=args.best_only)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

