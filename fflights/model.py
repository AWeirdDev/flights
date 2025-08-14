from dataclasses import dataclass


@dataclass
class Airline:
    code: str
    name: str


@dataclass
class Alliance:
    code: str
    name: str


@dataclass
class Metadata:
    airlines: list[Airline]
    alliances: list[Alliance]
