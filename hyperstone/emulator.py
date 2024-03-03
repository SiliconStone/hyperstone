import megastone as ms
from typing import TYPE_CHECKING, Type, Union

if TYPE_CHECKING:
    from .settings import SettingsType


class HyperEmu(ms.Emulator):
    def __init__(self, arch: ms.Architecture, settings: 'SettingsType'):
        super().__init__(arch)
        self.settings = settings

    def copy(self):
        """Create a copy of this Emulator, including memory and register state."""
        ctx = self.save_context()
        emu = HyperEmu(self.mem.arch, self.settings)
        emu.mem.load_memory(self.mem)
        emu.restore_context(ctx)
        return emu
