from dataclasses import dataclass
from functools import partial
from typing import Optional

from hyperstone.plugins.hooks.call_trace import CallTrace
from hyperstone.plugins.hooks.context import Context
from hyperstone.plugins.base import Plugin
from hyperstone.plugins.hooks.base import Hook, HookInfo
from hyperstone.util.logger import log


@dataclass(frozen=True)
class FunctionNullsubInfo:
    """
    Attributes:
        address: Address of the function to "patch"
        return_value: Return value of the function, if None, then don't change the return value
    """
    address: int
    return_value: Optional[int] = None


class FunctionNullsub(Plugin):
    """
    This plugin allows to turn a function into a nullsub, meaning that it would return instantly.
    An optional return value can be supplied
    """
    _INTERACT_TYPE = FunctionNullsubInfo

    def __init__(self, *args: FunctionNullsubInfo):
        self._call_trace_plugin: Optional[CallTrace] = None
        super().__init__(*args)

    def _prepare(self):
        for trace in Plugin.get_all_loaded(CallTrace, self.emu):
            self._call_trace_plugin = trace

    def _handle(self, obj: FunctionNullsubInfo):
        hook_plugin = Plugin.require(Hook, self.emu)
        hook_plugin.interact(HookInfo(f'Nullsub @ {obj.address:08X}', obj.address, None, partial(self._callback, obj, self._call_trace_plugin)))

    @staticmethod
    def _callback(stub: FunctionNullsubInfo, trace_plugin: Optional[CallTrace], ctx: Context):
        log.debug(f'Returning from {stub}')

        if trace_plugin is not None:
            trace_plugin.pop()

        retval = stub.return_value
        if retval is not None:
            retval = int(retval)
        ctx.emu.return_from_function(retval)
