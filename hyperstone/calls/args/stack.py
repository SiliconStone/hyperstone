from dataclasses import dataclass

from hyperstone.calls.args.base import Argument
from hyperstone.emulator import HyperEmu


@dataclass(frozen=True)
class Stack(Argument):
    offset: int

    def get(self, emu: HyperEmu) -> int:
        return emu.stack[self.offset]

    def set(self, emu: HyperEmu, value: int) -> None:
        emu.stack[self.offset] = value
