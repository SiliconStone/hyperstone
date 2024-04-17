from dataclasses import dataclass
from typing import Optional

from hyperstone import HyperEmu
from hyperstone.plugins.memory.streams.stream import Stream


@dataclass
class FileStream(Stream):
    filepath: str
    base: Optional[int] = None

    def raw(self, _: HyperEmu) -> bytes:
        with open(self.filepath, "rb") as f:
            return f.read()
