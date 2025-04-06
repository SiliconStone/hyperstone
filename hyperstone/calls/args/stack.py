from dataclasses import dataclass

from hyperstone.calls.args.base import Argument
from hyperstone.emulator import HyperEmu


@dataclass(frozen=True)
class Stack(Argument):
    offset: int
    is_reversed: bool = False
    needs_cleanup: bool = False

    def get(self, emu: HyperEmu) -> int:
        return emu.stack[self.offset]

    def set(self, emu: HyperEmu, value: int) -> None:
        # NOTE: set() shouldn't cleanup() since it is a "hard" set, only get() may need a cleanup(), sometimes
        emu.stack[self.offset] = value

    def cleanup(self, emu: HyperEmu) -> None:
        emu.stack.pop()
