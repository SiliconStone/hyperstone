from typing import Iterator

from hyperstone.calls import StackCall
from hyperstone.calls.args import Argument, Stack


class BaseStdCall(StackCall):
    def __init__(self, offset: int = 1, do_cleanup: bool = False) -> None:
        super().__init__(offset)
        self.do_cleanup = do_cleanup

    def __iter__(self) -> Iterator[Argument]:
        for var in super(BaseStdCall, self).__iter__():
            if isinstance(var, Stack):
                var = Stack(var.offset, is_reversed=True, needs_cleanup=self.do_cleanup)
            yield var


StdCall = BaseStdCall()
StdCallCleanup = BaseStdCall(do_cleanup=True)
