from dataclasses import dataclass
from typing import Optional

import megastone as ms

from hyperstone.plugins.memory.streams.stream import Stream
from hyperstone.emulator import HyperEmu
from hyperstone.util.logger import log


@dataclass
class CodeStream(Stream):
    assembly: str
    base: Optional[int] = None
    isa: Optional[ms.InstructionSet] = None

    def raw(self, emu: HyperEmu) -> bytes:
        if self.isa is None:
            self.isa = emu.mem.default_isa

        lines = len(self.assembly.split("\n"))
        log.info(f'Assembling {lines} lines for {self.isa} at 0x{self.base:08X}')
        return self.isa.assemble(self.assembly, self.base)
