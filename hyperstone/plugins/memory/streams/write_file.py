from dataclasses import dataclass

from hyperstone import HyperEmu
from hyperstone.plugins.memory.streams.stream import Stream


@dataclass
class FileStream(Stream):
    filepath: str

    def raw(self, _: HyperEmu) -> bytes:
        with open(self.filepath, "rb") as f:
            return f.read()
