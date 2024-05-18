from dataclasses import dataclass, field
from functools import partial
from typing import Optional, Callable, Any, Dict, Tuple, Union, List

import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSHookAlreadyRemovedError
from hyperstone.util.logger import log


@dataclass
class HookInfo:
    name: str
    address: Optional[Union[int, Callable[[], int]]]
    return_address: Optional[Union[int, Callable[[], int]]] = None
    callback: Optional[Callable[[HyperEmu, Dict[str, Any]], Any]] = None
    size: int = 1
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
    type: HookInfo
    obj: Optional[ms.Hook]


class Hook(Plugin):
    SILENT = '!'
    CTX_HOOK = '__hook__'

    def __init__(self, *hooks: HookInfo):
        super().__init__()
        self._interact_queue += hooks
        self._hooks: List[ActiveHook] = []

    def __getitem__(self, item: str) -> ActiveHook:
        for hook in self._hooks:
            if hook.type.name == item:
                return hook

    def get(self, hook_info: HookInfo) -> ActiveHook:
        for hook in self._hooks:
            if hook.type == hook_info:
                return hook

    @property
    def hooks(self) -> Tuple[ActiveHook, ...]:
        return tuple(self._hooks)

    def _handle(self, hook: HookInfo):
        ctx = {self.emu.CTX_GLOBAL: self.emu.context}
        func = partial(Hook._hook, hook, ctx)
        active = self.add_hook(hook, func, ms.HookType.CODE)
        ctx[self.CTX_HOOK] = active

    def add_hook(self, hook: HookInfo, func: Union[Callable[[HyperEmu], None], ms.HookFunc],
                 access_type: ms.HookType) -> ActiveHook:
        ms_hook = self.emu.add_hook(func, access_type, hook.address, hook.size)
        active = ActiveHook(hook, ms_hook)
        self._hooks.append(active)
        log.info(f'Added hook {hook.name}')
        return active

    def remove_hook(self, hook: ActiveHook):
        if not hook.obj:
            raise HSHookAlreadyRemovedError(f'Hook {hook.type.name} already removed')

        self._hooks.remove(hook)
        self.emu.remove_hook(hook.obj)
        hook.obj = None

    @staticmethod
    def _hook(hook_info: HookInfo, ctx: Dict[str, Any], emu: HyperEmu):
        if hook_info.return_address is None:
            was_called = hook_info.double_call
            hook_info.double_call = False
            if was_called:
                return
        else:
            hook_info.return_address = int(hook_info.return_address)

        log_fn = log.debug if hook_info.name.startswith(Hook.SILENT) else log.info

        log_fn(f'Hook - {hook_info.name} [PC = 0x{emu.pc:08X}, RET = 0x{emu.retaddr:08X}]')
        old_pc = emu.pc
        func = hook_info.callback
        if func:
            func(emu, ctx)

        if hook_info.return_address is not None:
            emu.pc = hook_info.return_address
        elif old_pc == emu.pc:
            hook_info.double_call = not hook_info.double_call
