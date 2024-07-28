from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.memory.streams.stream import Stream
from hyperstone.emulator import HyperEmu


@dataclass
class RawStream(Stream):
    """
    Represents a raw stream of data.
    The simplest stream, just contains some raw `bytes` at a chosen position (if supplied)
    This might be one of the most useful streams, as it should allow patching the memory almost directly.

    Attributes:
         data: The raw data of the stream.
         base: The base address of the stream. Usually used as a hint for mapping inside / as segments.
    """
    data: bytes
    base: Optional[int] = None

    def raw(self, _: HyperEmu) -> bytes:
        return self.data
