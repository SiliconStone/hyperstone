from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.memory.streams.stream import Stream
from hyperstone.emulator import HyperEmu


@dataclass
class RawStream(Stream):
    data: bytes
    base: Optional[int] = None

    def raw(self, _: HyperEmu) -> bytes:
        return self.data
