from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu
from hyperstone.util.logger import log


@dataclass
class Stream:
    @property
    def base(self) -> Optional[int]:
        return None

    @base.setter
    def base(self, value: Optional[int]):
        pass

    @staticmethod
    def raw(_: HyperEmu) -> bytes:
        return b''


class WriteStream(Plugin):
    """
    Generic stream writer plugin.
    """
    def __init__(self, *args: Stream):
        super().__init__(*args)

    def _handle(self, obj: Stream):
        if obj.base is None:
            raise ValueError(f'Cannot infer base address for {obj}')

        to_write = obj.raw(self.emu)
        self.emu.mem.write(obj.base, to_write)
        log.info(f'Wrote {len(to_write):08X} bytes to {obj.base:08X}...')
