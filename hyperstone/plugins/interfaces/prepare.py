from typing import Callable

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu

PrepareFunction = Callable[[HyperEmu], None]


class PreparePlugin(Plugin):
    """
    This plugin allows the user to supply functions to be executed before the emulator is started.
    This is useful when you need to set a few registers before a run, or allocate objects in the stack / heap.

    Notes:
        - This plugin just executes all the given functions on its prepare phase.
        - While this is useful for simple functions (commonly referred as hook functions / hook helpers), it may
            be noted that advanced behaviours should be implemented by creating a custom Plugin if needed.
        - Note that while this function doesn't have a Context object like hooks, it still has the global context
            which can and should be used here (emu.context)
    """
    def _handle(self, fn: PrepareFunction):
        fn(self.emu)
