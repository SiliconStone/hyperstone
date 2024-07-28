from typing import Any
import megastone as ms

from hyperstone.plugins.base import RunnerPlugin
from hyperstone.util.logger import log


class Entrypoint(RunnerPlugin):
    """
    Entrypoint for the emulator. Allows specifying an initial `PC` value.
    This is the most basic `RunnerPlugin`.

    Supports `LazyResolver`s

    Notes:
        - interact() does nothing in this plugin, as it is only useful as a RunnerPlugin (supplies run())
    """
    def _handle(self, obj: Any):
        pass

    def __init__(self, entrypoint: int = 0):
        super().__init__()
        self.entrypoint = entrypoint

    def _run_emu(self):
        """
        A method to run the emulator from a given entrypoint.
        A better plugin may override this method for a simpler, unified implementation.
        """
        self.emu.run(address=int(self.entrypoint))

    def _run(self):
        try:
            log.info(f'Running from {int(self.entrypoint):08X}...')
            self._run_emu()
        except ms.MemFaultError as f:
            log.error(f)
