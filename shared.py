import json
from typing import TypeVar, Type
from rsocket.frame_helpers import ensure_bytes
from rsocket.payload import Payload
from rsocket.helpers import utf8_decode

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Message:
    user: Optional[str] = None
    content: Optional[str] = None


def encode_dataclass(obj):
    return ensure_bytes(json.dumps(obj.__dict__))


T = TypeVar('T')


def decode_dataclass(data: bytes, cls: Type[T]) -> T:
    return cls(**json.loads(utf8_decode(data)))


def dataclass_to_payload(obj) -> Payload:
    return Payload(encode_dataclass(obj))
