from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.memory.streams.stream import Stream
from hyperstone.util.resolver import LazyResolver
from hyperstone.emulator import HyperEmu


@dataclass
class LazyStream(Stream):
    """
    Represents a stream of data that may be resolved later.
    Might be useful if referencing some python/hyperstone data that will be mapped much later.
    As for today, I still have no clue why this would be needed, but I needed more streams in `hyperstone`
    Do feel free to suggest / contribute by adding your own streams.

    Attributes:
        resolver: The resolver to be used when resolving data.
        base: The base address of the data. Usually used as a hint for mapping inside / as segments.
    """
    resolver: LazyResolver
    base: Optional[int] = None

    def raw(self, emu: HyperEmu) -> bytes:
        return bytes(self.resolver)
