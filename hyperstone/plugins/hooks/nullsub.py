from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.hooks.call_trace import CallTrace
from hyperstone.util.context import Context
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


class FunctionNullsubContext(Context):
    def __init__(self, stub: FunctionNullsubInfo, trace_plugin: Optional[CallTrace]):
        super().__init__()
        self.stub = stub
        self.trace_plugin = trace_plugin


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
        hook_plugin.interact(HookInfo(f'Nullsub @ {obj.address:08X}', obj.address, None, self._callback,
                                      ctx=FunctionNullsubContext(obj, self._call_trace_plugin), silent=True))

    @staticmethod
    def _callback(ctx: FunctionNullsubContext):
        log.debug(f'Returning from {ctx.stub}')

        if ctx.trace_plugin is not None:
            ctx.trace_plugin.pop()

        retval = ctx.stub.return_value
        if retval is not None:
            retval = int(retval)
        ctx.emu.return_from_function(retval)
