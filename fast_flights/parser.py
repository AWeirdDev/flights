from __future__ import annotations

import json
from typing import Any, Iterable

from selectolax.lexbor import LexborHTMLParser

from .fetch_result import FetchResult
from .model import (
    Airline,
    Airport,
    Alliance,
    CarbonEmission,
    Flights,
    JsMetadata,
    SimpleDatetime,
    SingleFlight,
)


class MetaList(list[Flights]):
    """Searched flights list, with metadata attached."""

    metadata: JsMetadata
    diagnostics: dict[str, object]


ERROR_RESPONSE = "type.googleapis.com/travel.frontend.flights.ErrorResponse"


def parse(source: str | bytes | FetchResult) -> MetaList:
    """Parse Google Flights HTML or captured XHR writeback responses."""

    if isinstance(source, FetchResult):
        remembered_empty: MetaList | None = None
        for body in source.xhr_bodies:
            xhr_result = parse_xhr_body(body)
            if xhr_result is None:
                continue
            if xhr_result or _status(xhr_result) in {
                "google_error_response",
                "empty_flight_payload",
                "malformed_flight_payload",
            }:
                return xhr_result
            remembered_empty = xhr_result

        html_result = _parse_html(source.html)
        if html_result or _status(html_result) != "missing_script_ds1":
            return html_result
        return remembered_empty or html_result

    if isinstance(source, bytes):
        source = source.decode("utf-8", errors="replace")
    return _parse_html(source or "")


def _parse_html(html: str) -> MetaList:
    parser = LexborHTMLParser(html or "")

    # find js
    script = parser.css_first(r"script.ds\:1")
    if script is None:
        return _empty("missing_script_ds1", source="html")
    return parse_js(script.text())


# Data discovery by @kftang, huge shout out!
def parse_js(js: str) -> MetaList:
    try:
        payload = json.loads(_extract_data_expr(js))
    except Exception as exc:
        return _empty("malformed_script_data", source="script.ds:1", detail=str(exc))
    return _parse_payload(payload, source="script.ds:1")


def parse_xhr_body(body: str | bytes) -> MetaList | None:
    """Parse a Google writeback body, returning None for unrelated XHRs."""

    try:
        frames = list(_google_json_frames(body))
    except Exception as exc:
        return _empty("malformed_xhr_body", source="xhr", detail=str(exc))

    saw_wrb = False
    remembered_empty: MetaList | None = None
    for frame in frames:
        for payload in _wrb_payloads(frame):
            saw_wrb = True
            try:
                decoded = json.loads(payload) if isinstance(payload, str) else payload
            except Exception as exc:
                remembered_empty = _empty(
                    "malformed_wrb_payload", source="xhr", detail=str(exc)
                )
                continue

            if _contains_error_response(decoded):
                return _empty("google_error_response", source="xhr")

            parsed = _parse_payload(decoded, source="xhr")
            if parsed:
                return parsed
            remembered_empty = parsed

    if remembered_empty is not None:
        return remembered_empty
    if saw_wrb:
        return _empty("no_parseable_xhr", source="xhr")
    return None


def _parse_payload(payload: Any, *, source: str) -> MetaList:
    if _contains_error_response(payload):
        return _empty("google_error_response", source=source)
    if not isinstance(payload, list):
        return _empty("malformed_flight_payload", source=source)

    alliances = []
    airlines = []

    try:
        alliances_data = payload[7][1][0] or []
        airlines_data = payload[7][1][1] or []
    except (IndexError, TypeError):
        alliances_data, airlines_data = [], []

    for row in alliances_data:
        if isinstance(row, list) and len(row) >= 2:
            alliances.append(Alliance(code=str(row[0]), name=str(row[1])))

    for row in airlines_data:
        if isinstance(row, list) and len(row) >= 2:
            airlines.append(Airline(code=str(row[0]), name=str(row[1])))

    meta = JsMetadata(alliances=alliances, airlines=airlines)

    flights = MetaList()
    flights.metadata = meta

    rows = list(_itinerary_rows(payload))
    if not rows:
        _set_diagnostics(flights, {"status": "empty_flight_payload", "source": source})
        return flights

    parse_errors = 0
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        try:
            flight = _flight_from_row(row)
        except Exception:
            parse_errors += 1
            continue

        key = _flight_key(flight)
        if key in seen:
            continue
        seen.add(key)
        flights.append(flight)

    _set_diagnostics(
        flights,
        {
            "status": "ok" if flights else "malformed_flight_payload",
            "source": source,
            "parse_errors": parse_errors,
        },
    )
    return flights


def _itinerary_rows(payload: list[Any]) -> Iterable[list[Any]]:
    for index in (2, 3):
        yield from _rows_from_block(_get(payload, index), depth=0)


def _rows_from_block(block: Any, *, depth: int) -> Iterable[list[Any]]:
    if depth > 4 or not isinstance(block, list):
        return
    if _is_itinerary_row(block):
        yield block
        return
    for item in block:
        if _is_itinerary_row(item):
            yield item
        elif isinstance(item, list):
            yield from _rows_from_block(item, depth=depth + 1)


def _is_itinerary_row(value: Any) -> bool:
    if not isinstance(value, list) or len(value) < 2:
        return False
    flight = value[0]
    return (
        isinstance(flight, list)
        and len(flight) > 22
        and isinstance(_get(flight, 2), list)
    )


def _flight_from_row(row: list[Any]) -> Flights:
    flight = row[0]
    sg_flights = [
        _single_flight_from_row(single_flight)
        for single_flight in (_get(flight, 2) or [])
        if isinstance(single_flight, list)
    ]
    extras = _get(flight, 22) or []

    return Flights(
        type=str(_get(flight, 0) or ""),
        price=_price_from_node(_get(row, 1)) or 0,
        airlines=[str(airline) for airline in (_get(flight, 1) or []) if airline],
        flights=sg_flights,
        carbon=CarbonEmission(
            typical_on_route=_as_int(_get(extras, 8)) or 0,
            emission=_as_int(_get(extras, 7)) or 0,
        ),
    )


def _single_flight_from_row(single_flight: list[Any]) -> SingleFlight:
    from_code = str(_get(single_flight, 3) or "")
    to_code = str(_get(single_flight, 6) or "")
    return SingleFlight(
        from_airport=Airport(
            code=from_code,
            name=str(_get(single_flight, 4) or from_code),
        ),
        to_airport=Airport(
            code=to_code,
            name=str(_get(single_flight, 5) or to_code),
        ),
        departure=SimpleDatetime(
            date=_date_tuple(_get(single_flight, 20)),
            time=_time_tuple(_get(single_flight, 8)),
        ),
        arrival=SimpleDatetime(
            date=_date_tuple(_get(single_flight, 21)),
            time=_time_tuple(_get(single_flight, 10)),
        ),
        duration=_as_int(_get(single_flight, 11)) or 0,
        plane_type=str(_get(single_flight, 17) or ""),
    )


def _google_json_frames(body: str | bytes) -> Iterable[Any]:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    text = text or ""
    if text.startswith(")]}'"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
    lines = [line for line in text.splitlines() if line.strip()]

    yielded = False
    for index, line in enumerate(lines):
        if line.strip().isdigit() and index + 1 < len(lines):
            yielded = True
            yield json.loads(lines[index + 1])

    if yielded:
        return

    stripped = "\n".join(lines).strip()
    if stripped:
        yield json.loads(stripped)


def _wrb_payloads(frame: Any) -> Iterable[Any]:
    if not isinstance(frame, list):
        return
    if frame and frame[0] == "wrb.fr":
        if len(frame) > 2 and frame[2] is not None:
            yield frame[2]
        for item in frame[3:]:
            if item is not None:
                yield item
        return
    for item in frame:
        yield from _wrb_payloads(item)


def _extract_data_expr(js: str) -> str:
    marker = "data:"
    start = js.find(marker)
    if start < 0:
        raise ValueError("script.ds:1 has no data field")
    pos = start + len(marker)
    while pos < len(js) and js[pos].isspace():
        pos += 1
    if pos >= len(js) or js[pos] not in "[{":
        return js[start + len(marker) :].rsplit(",", 1)[0]

    stack = ["]" if js[pos] == "[" else "}"]
    in_string = False
    quote = ""
    escape = False
    for end in range(pos + 1, len(js)):
        char = js[end]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                in_string = False
            continue

        if char in {'"', "'"}:
            in_string = True
            quote = char
        elif char in "[{":
            stack.append("]" if char == "[" else "}")
        elif char in "]}":
            if not stack or char != stack[-1]:
                raise ValueError("unbalanced data payload")
            stack.pop()
            if not stack:
                return js[pos : end + 1]

    raise ValueError("unterminated data payload")


def _contains_error_response(value: Any) -> bool:
    if isinstance(value, str):
        return ERROR_RESPONSE in value
    if isinstance(value, list):
        return any(_contains_error_response(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_error_response(item) for item in value.values())
    return False


def _empty(status: str, *, source: str, detail: str | None = None) -> MetaList:
    result = MetaList()
    diagnostic: dict[str, object] = {"status": status, "source": source}
    if detail:
        diagnostic["detail"] = detail
    result.metadata = JsMetadata(alliances=[], airlines=[], diagnostics=diagnostic)
    result.diagnostics = diagnostic
    return result


def _set_diagnostics(result: MetaList, diagnostics: dict[str, object]) -> None:
    result.diagnostics = diagnostics
    result.metadata.diagnostics = diagnostics


def _status(result: MetaList) -> str | None:
    diagnostics = getattr(result, "diagnostics", None)
    if isinstance(diagnostics, dict):
        status = diagnostics.get("status")
        return str(status) if status is not None else None
    meta_diagnostics = getattr(getattr(result, "metadata", None), "diagnostics", None)
    if isinstance(meta_diagnostics, dict):
        status = meta_diagnostics.get("status")
        return str(status) if status is not None else None
    return None


def _flight_key(flight: Flights) -> tuple[Any, ...]:
    legs = tuple(
        (
            leg.from_airport.code,
            leg.to_airport.code,
            leg.departure.date,
            leg.departure.time,
            leg.arrival.date,
            leg.arrival.time,
        )
        for leg in flight.flights
    )
    return (flight.price, tuple(flight.airlines), legs)


def _price_from_node(value: Any) -> int | None:
    direct = _as_int(value)
    if direct is not None:
        return direct
    if isinstance(value, list):
        for item in value:
            if isinstance(item, list) and len(item) > 1:
                nested = _as_int(item[1])
                if nested is not None:
                    return nested
        for item in value:
            nested = _price_from_node(item)
            if nested is not None:
                return nested
    return None


def _date_tuple(value: Any) -> tuple[int, int, int]:
    parts = _int_tuple(value)
    return (parts + (0, 0, 0))[:3]


def _time_tuple(value: Any) -> tuple[int, int]:
    parts = _int_tuple(value)
    return (parts + (0, 0))[:2]


def _int_tuple(value: Any) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    ints: list[int] = []
    for item in value:
        parsed = _as_int(item)
        if parsed is not None:
            ints.append(parsed)
    return tuple(ints)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _get(value: Any, index: int, default: Any = None) -> Any:
    try:
        return value[index]
    except (TypeError, IndexError):
        return default
