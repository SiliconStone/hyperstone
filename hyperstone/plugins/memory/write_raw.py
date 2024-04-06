from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.base import Plugin
from hyperstone.util.logger import log
@dataclass
class RawStream:
    data: bytes
    base: Optional[int] = None


class WriteRaw(Plugin):
    """
    Write raw stream to segment.
    """
    def __init__(self, *args: RawStream):
        super().__init__(*args)

    def _handle(self, obj: RawStream):
        if obj.base is None:
            raise ValueError(f'Cannot infer base address for {obj}')
        self.emu.mem.write(obj.base, obj.data)
        log.info(f'Wrote {len(obj.data):08X} bytes to {obj.base:08X}...')
