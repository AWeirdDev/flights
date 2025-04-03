import abc
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, List, Generic, Optional, Sequence, TypeVar, Union
from typing_extensions import TypeAlias, override

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
    def decode(cls, root: NLData) -> ...:
        ...


# Type Aliases
AirlineCode: TypeAlias = str
AirlineName: TypeAlias = str

@dataclass
class Flight:
    operator: str

@dataclass
class Itinerary:
    airline_code: AirlineCode
    airline_names: List[AirlineName]
    flights: List[Flight]

@dataclass
class Result:
    best: List[Itinerary]
    other: List[Itinerary]

    # airport_details: Any
    # unknown_1: Any

class FlightDecoder(Decoder):
    operator: DecoderKey[AirlineName] = DecoderKey([2])

    @classmethod
    @override
    def decode(cls, root: NLData) -> List[Flight]:
        return [Flight(**cls.decode_el(NLData(el))) for el in root]

class ItineraryDecoder(Decoder):
    AIRLINE_CODE: DecoderKey[AirlineCode] = DecoderKey([0, 0])
    AIRLINE_NAMES: DecoderKey[List[AirlineName]] = DecoderKey([0, 1])
    FLIGHTS: DecoderKey[List[Flight]] = DecoderKey([0, 2], FlightDecoder.decode)

    @classmethod
    @override
    def decode(cls, root: NLData) -> List[Itinerary]:
        return [Itinerary(**cls.decode_el(NLData(el))) for el in root]


class ResultDecoder(Decoder):
    # UNKNOWN_1: DecoderKey[Any] = DecoderKey([0])
    # AIRPORT_DETAILS: DecoderKey[Any] = DecoderKey([1])
    BEST: DecoderKey[List[Itinerary]] = DecoderKey([2, 0], ItineraryDecoder.decode)
    OTHER: DecoderKey[List[Itinerary]] = DecoderKey([3, 0], ItineraryDecoder.decode)

    @classmethod
    @override
    def decode(cls, root: NLData) -> Result:
        return Result(**cls.decode_el(root))


