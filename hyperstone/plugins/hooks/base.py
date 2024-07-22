from dataclasses import dataclass, field
from functools import partial
from typing import Optional, Callable, Any, Tuple, Union, List, TypeVar

import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSHookAlreadyRemovedError
from hyperstone.util.logger import log
from hyperstone.plugins.hooks.context import Context, DictContext


HookFunc = Callable[[HyperEmu], Any]
HyperstoneCallback = Callable[[Context], Any]
KC = TypeVar('KC', bound=Context)  # Support for old python


@dataclass
class HookInfo:
    name: str
    address: Optional[Union[int, Callable[[], int]]]
    return_address: Optional[Union[int, Callable[[], int]]] = None
    callback: Optional[HyperstoneCallback] = None
    size: int = 1
    ctx: KC = field(default_factory=DictContext)
    double_call: bool = False

    _address: Union[int, Callable[[], int]] = field(init=False, repr=False)

    @property
    def address(self):
        return int(self._address) if self._address is not None else None

    @address.setter
    def address(self, value):
        self._address = value


@dataclass
class ActiveHook:
    info: HookInfo
    obj: Optional[ms.Hook]


class Hook(Plugin):
    SILENT = '!'

    def __init__(self, *hooks: HookInfo):
        super().__init__()
        self._interact_queue += hooks
        self._hooks: List[ActiveHook] = []

    def __getitem__(self, item: str) -> ActiveHook:
        for hook in self._hooks:
            if hook.info.name == item:
                return hook

    def get(self, hook_info: HookInfo) -> ActiveHook:
        for hook in self._hooks:
            if hook.info == hook_info:
                return hook

    @property
    def hooks(self) -> Tuple[ActiveHook, ...]:
        return tuple(self._hooks)

    def _handle(self, hook: HookInfo):
        func = partial(Hook._hook, hook.ctx)
        hook.ctx.hook = self.add_hook(hook, func, ms.HookType.CODE)

    def add_hook(self, hook: HookInfo, func: Union[HookFunc, ms.HookFunc],
                 access_type: ms.HookType) -> ActiveHook:
        ms_hook = self.emu.add_hook(func, access_type, hook.address, hook.size)
        active = ActiveHook(hook, ms_hook)
        self._hooks.append(active)
        log.info(f'Added hook {hook.name}')
        return active

    def remove_hook(self, hook: ActiveHook):
        if not hook.obj:
            raise HSHookAlreadyRemovedError(f'Hook {hook.info.name} already removed')

        self._hooks.remove(hook)
        self.emu.remove_hook(hook.obj)
        hook.obj = None

    @staticmethod
    def _hook(hook_ctx: Context, emu: HyperEmu):
        hook_info = hook_ctx.hook.info
        hook_ctx.emu = emu

        if hook_info.return_address is None:
            was_called = hook_info.double_call
            hook_info.double_call = False
            if was_called:
                return
        else:
            hook_info.return_address = int(hook_info.return_address)

        log_fn = log.trace if hook_info.name.startswith(Hook.SILENT) else log.info

        log_fn(f'Hook - {hook_info.name} [PC = 0x{emu.pc:08X}, RET = 0x{emu.retaddr:08X}]')
        old_pc = emu.pc
        func = hook_info.callback
        if func:
            try:
                func(hook_ctx)
            except Exception as e:
                log.error(f'Error calling {func}: {e}')

        if hook_info.return_address is not None:
            emu.pc = hook_info.return_address
        elif old_pc == emu.pc:
            hook_info.double_call = not hook_info.double_call
