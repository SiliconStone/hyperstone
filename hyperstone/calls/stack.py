from typing import Iterator

from hyperstone.calls.args import Argument
from hyperstone.calls.args.stack import Stack
from hyperstone.calls.base import CallingConvention


class StackCall(CallingConvention):
    def __init__(self, offset: int = 1):
        super().__init__()
        self.offset = offset

    def __iter__(self) -> Iterator[Argument]:
        offset = self.offset
        while True:
            yield Stack(offset)
            offset += 1
