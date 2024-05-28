from typing import Iterator
import megastone as ms

from hyperstone.calls.args import Argument
from hyperstone.calls.args.register import Register
from hyperstone.calls.base import CallingConvention


class RegisterCall(CallingConvention):
    def __init__(self, *registers: ms.Register):
        super().__init__()
        self.regs = registers

    def __iter__(self) -> Iterator[Argument]:
        regs = self.regs
        for reg in regs:
            yield Register(reg)
