from typing import Any

def make_tfs(
    flights_data: list[dict[str, Any]],
    seat_data: str,
    passengers_data: list[str],
    trip_data: str,
) -> Tfs: ...

class Tfs:
    def bytes(self) -> bytes: ...
    def base64(self) -> str: ...

def generate_trail() -> str: ...
