from typing import Callable

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu

PrepareFunction = Callable[[HyperEmu], None]

class PreparePlugin(Plugin):
    def _handle(self, fn: PrepareFunction):
        fn(self.emu)
