from typing import Any, Optional
import megastone as ms

from hyperstone.plugins.base import RunnerPlugin
from hyperstone.util.logger import log


class GDBServer(RunnerPlugin):
    def _handle(self, obj: Any):
        pass

    def __init__(self, host: str = 'localhost', port: int = 1234):
        super().__init__()
        self.host = host
        self.port = port
        self._gdbserver: Optional[ms.GDBServer] = None

    def _run(self):
        log.info(f'Starting GDB Server')
        self._gdbserver = ms.GDBServer(self.emu, host=self.host, port=self.port)
        try:
            self._gdbserver.run()
        except ms.MemFaultError as f:
            log.error(f)
