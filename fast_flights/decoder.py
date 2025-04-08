import abc
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, List, Generic, Optional, Sequence, TypeVar, Union, Tuple
from typing_extensions import TypeAlias, override

from .flights_impl import ItinerarySummary

DecodePath: TypeAlias = List[int]
NLBaseType: TypeAlias = Union[int, str, None, Sequence['NLBaseType']]

# N(ested)L(ist)Data, this class allows indexing using a path, and as an int to make
# traversal easier within the nested list data
@dataclass
class NLData(Sequence[NLBaseType]):
    data: List[NLBaseType]

    def __getitem__(self, decode_path: Union[int, DecodePath]) -> NLBaseType:
        if isinstance(decode_path, int):
            return self.data[decode_path]
        it = self.data
        for index in decode_path:
            assert isinstance(it, list), f'Found non list type while trying to decode {decode_path}'
            assert index < len(it), f'Trying to traverse to index out of range when decoding {decode_path}'
            it = it[index]
        return it

    @override
    def __len__(self) -> int:
        return len(self.data)

# DecoderKey is used to specify the path to a field from a decoder class
V = TypeVar('V')
@dataclass
class DecoderKey(Generic[V]):
    decode_path: DecodePath
    decoder: Optional[Callable[[NLData], V]] = None

    def decode(self, root: NLData) -> Union[NLBaseType, V]:
        data = root[self.decode_path]
        if isinstance(data, list) and self.decoder:
            assert self.decoder is not None, f'decoder should be provided in order to further decode NLData instances'
            return self.decoder(NLData(data))
        return data

# Decoder is used to aggregate all fields and their paths
class Decoder(abc.ABC):
    @classmethod
    def decode_el(cls, el: NLData) -> Mapping[str, Any]:
        decoded: Mapping[str, Any] = {}
        for field_name, key_decoder in vars(cls).items():
            if isinstance(key_decoder, DecoderKey):
                value = key_decoder.decode(el)
                decoded[field_name.lower()] = value
        return decoded

    @classmethod
    def decode(cls, root: Union[list, NLData]) -> ...:
        ...


# Type Aliases
AirlineCode: TypeAlias = str
AirlineName: TypeAlias = str
AirportCode: TypeAlias = str
AirportName: TypeAlias = str
ProtobufStr: TypeAlias = str
Minute: TypeAlias = int

@dataclass
class Codeshare:
    airline_code: AirlineCode
    flight_number: int
    airline_name: AirlineName

@dataclass
class Flight:
    airline: AirlineCode
    airline_name: AirlineName
    flight_number: str
    operator: str
    codeshares: List[Codeshare]
    aircraft: str
    departure_airport: AirportCode
    departure_airport_name: AirportName
    arrival_airport: AirportCode
    arrival_airport_name: AirportName
    # some_enum: int
    # some_enum: int
    departure_date: Tuple[int, int, int]
    arrival_date: Tuple[int, int, int]
    departure_time: Tuple[int, int]
    arrival_time: Tuple[int, int]
    travel_time: int
    seat_pitch_short: str
    # seat_pitch_long: str

@dataclass
class Layover:
    minutes: Minute
    departure_airport: AirportCode
    departure_airport_name: AirportName
    departure_airport_city: AirportName
    arrival_airport: AirportCode
    arrival_airport_name: AirportName
    arrival_airport_city: AirportName

@dataclass
class Itinerary:
    airline_code: AirlineCode
    airline_names: List[AirlineName]
    flights: List[Flight]
    layovers: List[Layover]
    travel_time: int
    departure_airport: AirportCode
    arrival_airport: AirportCode
    departure_date: Tuple[int, int, int]
    arrival_date: Tuple[int, int, int]
    departure_time: Tuple[int, int]
    arrival_time: Tuple[int, int]
    itinerary_summary: ItinerarySummary

@dataclass
class DecodedResult:
    # raw unparsed data
    raw: list

    best: List[Itinerary]
    other: List[Itinerary]

    # airport_details: Any
    # unknown_1: Any

class CodeshareDecoder(Decoder):
    AIRLINE_CODE: DecoderKey[AirlineCode] = DecoderKey([0])
    FLIGHT_NUMBER: DecoderKey[str] = DecoderKey([1])
    AIRLINE_NAME: DecoderKey[List[AirlineName]] = DecoderKey([3])

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData]) -> List[Codeshare]:
        return [Codeshare(**cls.decode_el(NLData(el))) for el in root]

class FlightDecoder(Decoder):
    OPERATOR: DecoderKey[AirlineName] = DecoderKey([2])
    DEPARTURE_AIRPORT: DecoderKey[AirportCode] = DecoderKey([3])
    DEPARTURE_AIRPORT_NAME: DecoderKey[AirportName] = DecoderKey([4])
    ARRIVAL_AIRPORT: DecoderKey[AirportCode] = DecoderKey([5])
    ARRIVAL_AIRPORT_NAME: DecoderKey[AirportName] = DecoderKey([6])
    # SOME_ENUM: DecoderKey[int] = DecoderKey([7])
    # SOME_ENUM: DecoderKey[int] = DecoderKey([9])
    DEPARTURE_TIME: DecoderKey[Tuple[int, int]] = DecoderKey([8])
    ARRIVAL_TIME: DecoderKey[Tuple[int, int]] = DecoderKey([10])
    TRAVEL_TIME: DecoderKey[int] = DecoderKey([11])
    SEAT_PITCH_SHORT: DecoderKey[str] = DecoderKey([14])
    AIRCRAFT: DecoderKey[str] = DecoderKey([17])
    DEPARTURE_DATE: DecoderKey[Tuple[int, int, int]] = DecoderKey([20])
    ARRIVAL_DATE: DecoderKey[Tuple[int, int, int]] = DecoderKey([21])
    AIRLINE: DecoderKey[AirlineCode] = DecoderKey([22, 0])
    AIRLINE_NAME: DecoderKey[AirlineName] = DecoderKey([22, 3])
    FLIGHT_NUMBER: DecoderKey[str] = DecoderKey([22, 1])
    # SEAT_PITCH_LONG: DecoderKey[str] = DecoderKey([30])
    CODESHARES: DecoderKey[List[Codeshare]] = DecoderKey([15], CodeshareDecoder.decode)

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData]) -> List[Flight]:
        return [Flight(**cls.decode_el(NLData(el))) for el in root]

class LayoverDecoder(Decoder):
    MINUTES: DecoderKey[int] = DecoderKey([0])
    DEPARTURE_AIRPORT: DecoderKey[AirportCode] = DecoderKey([1])
    DEPARTURE_AIRPORT_NAME: DecoderKey[AirportName] = DecoderKey([4])
    DEPARTURE_AIRPORT_CITY: DecoderKey[AirportName] = DecoderKey([5])
    ARRIVAL_AIRPORT: DecoderKey[AirportCode] = DecoderKey([2])
    ARRIVAL_AIRPORT_NAME: DecoderKey[AirportName] = DecoderKey([6])
    ARRIVAL_AIRPORT_CITY: DecoderKey[AirportName] = DecoderKey([7])

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData]) -> List[Layover]:
        return [Layover(**cls.decode_el(NLData(el))) for el in root]

class ItineraryDecoder(Decoder):
    AIRLINE_CODE: DecoderKey[AirlineCode] = DecoderKey([0, 0])
    AIRLINE_NAMES: DecoderKey[List[AirlineName]] = DecoderKey([0, 1])
    FLIGHTS: DecoderKey[List[Flight]] = DecoderKey([0, 2], FlightDecoder.decode)
    DEPARTURE_AIRPORT: DecoderKey[AirportCode] = DecoderKey([0, 3])
    DEPARTURE_DATE: DecoderKey[Tuple[int, int, int]] = DecoderKey([0, 4])
    DEPARTURE_TIME: DecoderKey[Tuple[int, int]] = DecoderKey([0, 5])
    ARRIVAL_AIRPORT: DecoderKey[AirportCode] = DecoderKey([0, 6])
    ARRIVAL_DATE: DecoderKey[Tuple[int, int, int]] = DecoderKey([0, 7])
    ARRIVAL_TIME: DecoderKey[Tuple[int, int]] = DecoderKey([0, 8])
    TRAVEL_TIME: DecoderKey[int] = DecoderKey([0, 9])
    # UNKNOWN: DecoderKey[int] = DecoderKey([0, 10])
    LAYOVERS: DecoderKey[List[Layover]] = DecoderKey([0, 13], LayoverDecoder.decode)
    # first field of protobuf is the same as [0, 4] on the root? seems like 0,4 is for tracking
    # contains a summary of the flight numbers and the price (as a fixed point sint)
    ITINERARY_SUMMARY: DecoderKey[ItinerarySummary] = DecoderKey([1], lambda data: ItinerarySummary.from_b64(data[1]))
    # contains Flight(s), the price, and a few more
    # FLIGHTS_PROTOBUF: DecoderKey[ProtobufStr] = DecoderKey([8])
    # some struct containing emissions info
    # EMISSIONS: DecoderKey[Emissions] = DecoderKey([22])

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData]) -> List[Itinerary]:
        return [Itinerary(**cls.decode_el(NLData(el))) for el in root]


class ResultDecoder(Decoder):
    # UNKNOWN_1: DecoderKey[Any] = DecoderKey([0])
    # AIRPORT_DETAILS: DecoderKey[Any] = DecoderKey([1])
    BEST: DecoderKey[List[Itinerary]] = DecoderKey([2, 0], ItineraryDecoder.decode)
    OTHER: DecoderKey[List[Itinerary]] = DecoderKey([3, 0], ItineraryDecoder.decode)

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData]) -> DecodedResult:
        assert isinstance(root, list), 'Root data must be list type'
        return DecodedResult(**cls.decode_el(NLData(root)), raw=root)
