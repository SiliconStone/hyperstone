from dataclasses import dataclass, field
from functools import partial
from typing import Optional, Callable, Any, Dict, Tuple, Union

import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu
from hyperstone.util import log


@dataclass
class HookType:
    name: str
    return_address: int
    address: Union[int, Callable[[], int]]
    return_address: Union[int, Callable[[], int]]
    callback: Optional[Callable[[HyperEmu, Dict[str, Any]], Any]] = None
    double_call: bool = False
    _address: Union[int, Callable[[], int]] = field(init=False, repr=False)
    _return_address: Union[int, Callable[[], int]] = field(init=False, repr=False)

    @property
    def address(self):
        return int(self._address)

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def return_address(self):
        return int(self._return_address)

    @return_address.setter
    def return_address(self, value):
        self._return_address = value


@dataclass
class ActiveHook:
    type: HookType
    obj: ms.Hook


class Hooks(Plugin):
    SILENT = '!'

    def __init__(self, *hooks: HookType):
        super().__init__()
        self._interact_queue += hooks
        self._hooks = []

    @property
    def hooks(self) -> Tuple[ActiveHook, ...]:
        return tuple(self._hooks)

    def _handle_interact(self, *hooks: HookType):
        for hook in hooks:
            start = hook.address
            ctx = {self.emu.CTX_GLOBAL: self.emu.context}
            func = partial(Hooks._hook, hook, ctx)
            emu_hook = self.emu.add_code_hook(func, start)

            self._hooks.append(ActiveHook(hook, emu_hook))
            log.info(f'Added hook {hook.name}')

    @staticmethod
    def _hook(hook_type: HookType, ctx: Dict[str, Any], emu: HyperEmu):
        if not hook_type.return_address:
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
