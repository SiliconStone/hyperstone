from dataclasses import dataclass, field
from functools import partial
from typing import Optional, Callable, Any, Dict, Tuple, Union, List

import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSHookAlreadyRemovedError
from hyperstone.util import log


@dataclass
class HookType:
    name: str
    address: Optional[Union[int, Callable[[], int]]]
    return_address: Optional[Union[int, Callable[[], int]]]
    callback: Optional[Callable[[HyperEmu, Dict[str, Any]], Any]] = None
    size: int = 1
    double_call: bool = False

    _address: Union[int, Callable[[], int]] = field(init=False, repr=False)
    _return_address: Union[int, Callable[[], int]] = field(init=False, repr=False)

    @property
    def address(self):
        return int(self._address) if self._address is not None else None

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def return_address(self):
        return int(self._return_address) if self._return_address is not None else None

    @return_address.setter
    def return_address(self, value):
        self._return_address = value


@dataclass
class ActiveHook:
    type: HookType
    obj: Optional[ms.Hook]


class Hooks(Plugin):
    SILENT = '!'

    def __init__(self, *hooks: HookType):
        super().__init__()
        self._interact_queue += hooks
        self._hooks: List[ActiveHook] = []

    def __getitem__(self, item: str) -> ActiveHook:
        for hook in self._hooks:
            if hook.type.name == item:
                return hook

    def get(self, hook_type: HookType) -> ActiveHook:
        for hook in self._hooks:
            if hook.type == hook_type:
                return hook

    @property
    def hooks(self) -> Tuple[ActiveHook, ...]:
        return tuple(self._hooks)

    def _handle(self, hook: HookType):
        ctx = {self.emu.CTX_GLOBAL: self.emu.context}
        func = partial(Hooks._hook, hook, ctx)
        self.add_hook(hook, func, ms.HookType.CODE)

    def add_hook(self, hook: HookType, func: Union[Callable[[HyperEmu], None], ms.HookFunc],
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
    def _hook(hook_type: HookType, ctx: Dict[str, Any], emu: HyperEmu):
        if hook_type.return_address is None:
            was_called = hook_type.double_call
            hook_type.double_call = False
            if was_called:
                return

        log_fn = log.debug if hook_type.name.startswith(Hooks.SILENT) else log.info

        log_fn(f'Hook - {hook_type.name} [PC = 0x{emu.pc:08X}, RET = 0x{emu.retaddr:08X}]')
        old_pc = emu.pc
        func = hook_type.callback
        if func:
            func(emu, ctx)

        if hook_type.return_address is not None:
            emu.pc = hook_type.return_address
        elif old_pc == emu.pc:
            hook_type.double_call = not hook_type.double_call