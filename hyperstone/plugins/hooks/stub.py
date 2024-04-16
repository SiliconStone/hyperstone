from dataclasses import dataclass
from functools import partial
from typing import Optional, Union, Callable

from hyperstone.plugins.hooks.base import Hook, HookInfo
from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu


@dataclass(frozen=True)
class FunctionStubInfo:
    address: int
    return_value: Optional[int] = None


class FunctionStub(Plugin):
    _INTERACT_TYPE = FunctionStubInfo
    def _handle(self, obj: FunctionStubInfo):
        hook_plugin = Plugin.require(Hook, self.emu)
        hook_plugin.interact(HookInfo(f'Stub @ {obj.address:08X}', obj.address, None, partial(self._callback, obj)))

    @staticmethod
    def _callback(stub: FunctionStubInfo, emu: HyperEmu, _):
        retval = stub.return_value
        if retval is not None:
            retval = int(retval)
        emu.return_from_function(retval)
