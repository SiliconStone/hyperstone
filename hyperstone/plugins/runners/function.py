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
        sp = self.emu.sp
        self.emu.sp += self.emu.arch.word_size  # Allocate a spot for the push that is done via megastone's run_function()
        try:
            self.emu.run_function(int(self.entrypoint))
            self.emu.sp = sp  # To keep the stack sane (the pushed value will be popped via callee)
            # try-finally block to not catch an exception but to restore SP only if no exception was caught
        finally:
            pass
