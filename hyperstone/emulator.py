from typing import TYPE_CHECKING

import megastone as ms

if TYPE_CHECKING:
    from hyperstone.settings import SettingsType


class HyperEmu(ms.Emulator):
    def __init__(self, arch: ms.Architecture, settings: 'SettingsType'):
        super().__init__(arch)
        self.settings = settings
        self.context = dict()

    def copy(self):
        """Create a copy of this Emulator, including memory and register state."""
        ctx = self.save_context()
        emu = HyperEmu(self.mem.arch, self.settings)
        emu.context = self.context
        emu.mem.load_memory(self.mem)
        emu.restore_context(ctx)
        return emu

    @property
    def retaddr(self) -> int:
        if self.arch.retaddr_reg is not None:
            return self.regs.retaddr
        else:
            return self.stack[0]
