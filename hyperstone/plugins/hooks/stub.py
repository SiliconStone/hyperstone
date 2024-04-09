from dataclasses import dataclass
from functools import partial
from typing import Optional, Union, Callable

from hyperstone.plugins.hooks.base import Hooks, HookType
from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu


@dataclass(frozen=True)
class StubInfo:
    address: int
    return_value: Optional[int] = None


class FunctionStub(Plugin):
    _INTERACT_TYPE = StubInfo
    def _handle(self, obj: StubInfo):
        hook_plugin = Plugin.require(Hooks, self.emu)
        hook_plugin.interact(HookType(f'Stub @ {obj.address:08X}', obj.address, None, partial(self._callback, obj)))

    @staticmethod
    def _callback(stub: StubInfo, emu: HyperEmu, _):
        emu.return_from_function(stub.return_value)
