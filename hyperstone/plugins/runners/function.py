from hyperstone.plugins.runners.entrypoint import Entrypoint


class FunctionEntrypoint(Entrypoint):
    def _run_emu(self):
        self.emu.run_function(int(self.entrypoint))
