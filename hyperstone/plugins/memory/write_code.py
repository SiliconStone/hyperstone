from dataclasses import dataclass
from typing import Optional

import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.util.logger import log


@dataclass
class CodeStream:
    assembly: str
    base: Optional[int] = None
    isa: Optional[ms.InstructionSet] = None


class WriteCode(Plugin):
    """
    Write code to segment.
    """
    def __init__(self, *args: CodeStream):
        super().__init__(*args)

    def _handle(self, obj: CodeStream):
        if obj.base is None:
            raise ValueError(f'Cannot infer base address for {obj}')
        write_size = self.emu.mem.write_code(obj.base, obj.assembly, obj.isa)
        log.info(f'Wrote {write_size:08X} bytes to {obj.base:08X}...')

