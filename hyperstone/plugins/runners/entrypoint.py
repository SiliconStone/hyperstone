from typing import Any
import megastone as ms

from hyperstone.plugins.base import RunnerPlugin
from hyperstone.util import log


class Entrypoint(RunnerPlugin):
    def _handle_interact(self, *objs: Any):
        pass

    def __init__(self, entrypoint: int = 0):
        super().__init__()
        self.entrypoint = entrypoint

    def _run_emu(self):
        self.emu.run(address=self.entrypoint)

    def _run(self):
        try:
            log.info(f'Running from {self.entrypoint:08X}...')
            self._run_emu()
        except ms.MemFaultError as f:
            log.error(f)