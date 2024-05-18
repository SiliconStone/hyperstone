from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.memory.streams.stream import Stream
from hyperstone.util.resolver import LazyResolver
from hyperstone.emulator import HyperEmu


@dataclass
class LazyStream(Stream):
    resolver: LazyResolver
    base: Optional[int] = None

    def raw(self, emu: HyperEmu) -> bytes:
        return bytes(self.resolver)
