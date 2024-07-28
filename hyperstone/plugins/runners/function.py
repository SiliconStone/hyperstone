from hyperstone.plugins.runners.entrypoint import Entrypoint


class FunctionEntrypoint(Entrypoint):
    """
    Implements an Entrypoint at the beginning of a function.
    Will stop execution normally when encountering a final "Return" statement.

    Notes:
        Internally, megastone allocates a segment called `ret_flag`, this segment's address is pushed onto the stack
        and when the emulator runs in this execute-only segment, the emulator will stop execution.
    """
    def _run_emu(self):
        self.emu.run_function(int(self.entrypoint))
