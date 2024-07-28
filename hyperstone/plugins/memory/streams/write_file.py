from dataclasses import dataclass
from typing import Optional

from hyperstone.emulator import HyperEmu
from hyperstone.plugins.memory.streams.stream import Stream


@dataclass
class FileStream(Stream):
    """
    Represents a stream of data from a file on the disk.

    Attributes:
        filepath: The path to the file with the data, will be opened in binary mode.
        base: The base address of the stream. Usually used as a hint for mapping inside / as segments.
    """
    filepath: str
    base: Optional[int] = None

    def raw(self, _: HyperEmu) -> bytes:
        with open(self.filepath, 'rb') as f:
            return f.read()
