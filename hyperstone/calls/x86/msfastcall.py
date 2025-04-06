from typing import Iterator

from hyperstone.calls import CallingConvention, RegisterCall, CDecl
from hyperstone.calls.args import Argument
from hyperstone.calls.x86.base import REGS


class X86MSFastCall(CallingConvention):
    def __iter__(self) -> Iterator[Argument]:
        yield from RegisterCall(
            REGS.ecx,
            REGS.edx,
        )

        yield from CDecl()
