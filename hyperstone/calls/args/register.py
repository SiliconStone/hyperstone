from dataclasses import dataclass
import megastone as ms

from hyperstone.calls.args.base import Argument
from hyperstone.emulator import HyperEmu
from hyperstone.util.logger import log


@dataclass(frozen=True)
class Register(Argument):
    register: ms.Register

    def get(self, emu: HyperEmu) -> int:
        return emu.regs.read(self.register)

    def set(self, emu: HyperEmu, value: int) -> None:
        emu.regs.write(self.register, value)
