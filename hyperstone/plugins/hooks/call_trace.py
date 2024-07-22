from dataclasses import dataclass
import enum
from typing import Optional, List, Dict, NewType

import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.plugins.hooks.base import Hook, ActiveHook, HookInfo
from hyperstone.plugins.hooks.context import Context
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSPluginBadStateError
from hyperstone.util.logger import log


EmuAddress = NewType("EmuAddress", int)
EmuOpcode = NewType("EmuOpcode", int)


class CallTraceEnum(enum.Enum):
    Normal = enum.auto()
    Call = enum.auto()
    Return = enum.auto()


@dataclass
class CallTraceCache:
    hits: int
    value: CallTraceEnum


class CallTraceContext(Context):
    """
    The context implementation required for the `CallTrace` plugin
    Used internally by the `_CallTraceHook` hook

    This class is highly optimised to resolve call opcodes.
    """
    def __init__(self, sensitivity: int):
        super().__init__()
        self.last_pc: Optional[int] = None
        self.pc: Optional[int] = None
        self.trace: List[int] = []
        self.sensitivity = sensitivity
        self.l1_cache_sensitivity = 4
        self.l2_cache_sensitivity = 64
        self._l1_cache: Dict[EmuOpcode, CallTraceCache] = {}
        self._l2_cache: Dict[EmuAddress, CallTraceCache] = {}

    def reset(self):
        self.last_pc = None
        self.pc = None
        self.trace.clear()
        self._l1_cache.clear()
        self._l2_cache.clear()

    def _check_call_slow(self) -> CallTraceEnum:
        insn_addr = EmuAddress(self.last_pc)

        if insn_addr in self._l2_cache:
            return self._l2_cache[insn_addr].value

        opcode = EmuOpcode(self.emu.mem.read(self.last_pc, self.l1_cache_sensitivity))
        if opcode in self._l1_cache:
            cache = self._l1_cache[opcode]
            cache.hits += 1
            if cache.hits > self.l2_cache_sensitivity:
                self._l2_cache[insn_addr] = CallTraceCache(0, cache.value)

            return cache.value

        # Now our magic trick, megastone
        insn = self.emu.mem.disassemble_one(self.last_pc)
        if insn.is_call or insn.is_interrupt:
            value = CallTraceEnum.Call
        elif insn.is_ret or insn.is_iret:
            value = CallTraceEnum.Return
        else:
            value = CallTraceEnum.Normal
        self._l1_cache[opcode] = CallTraceCache(1, value)
        return value

    def _check_call(self) -> CallTraceEnum:
        if self.last_pc is None or self.pc is None:
            return CallTraceEnum.Normal
        if self.emu is None:
            return CallTraceEnum.Normal

        if abs(self.pc - self.last_pc) < self.sensitivity:
            # Too low for a call
            return CallTraceEnum.Normal

        return self._check_call_slow()

    def next(self) -> CallTraceEnum:
        self.last_pc = self.pc
        self.pc = self.emu.pc

        return self._check_call()


class CallTrace(Plugin):
    def __init__(self, sensitivity: int = 8):
        self._hook: Optional[ActiveHook] = None
        self._hook_plugin: Optional[Hook] = None
        self._sensitivity = sensitivity
        log.warning('This plugin is fairly slow (and spammy). It adds a global code Hook which chokes on Unicorn\'s '
                    'internal code hook handler and register read handler. Use with caution!')
        super().__init__()

    def _prepare(self):
        self._hook_plugin = Plugin.require(Hook, self.emu)
        self._hook_plugin.prepare(self.emu)

        self._hook = self._hook_plugin.add_hook(
            HookInfo(
                name='_CallTraceHook',
                address=None,
                ctx=CallTraceContext(self._sensitivity),
            ),
            self._callback,
            ms.HookType.CODE
        )
        self._hook.info.ctx.hook = self._hook
        self._hook.info.ctx.emu = self.emu

    def pop(self):
        if self._hook is None:
            raise HSPluginBadStateError('Cannot pop without installing hook first')

        self._handle_call_type(CallTraceEnum.Return)

    def _callback(self, _: HyperEmu):
        ctx: CallTraceContext = self._hook.info.ctx
        call_type = ctx.next()
        self._handle_call_type(call_type)

    def _handle_call_type(self, call_type: CallTraceEnum):
        ctx: CallTraceContext = self._hook.info.ctx
        if call_type == CallTraceEnum.Normal:
            return
        elif call_type == CallTraceEnum.Call:
            ctx.trace.append(self.emu.pc)
            log.debug(f'Entering: \t{self.emu.pc:#X}')
        elif call_type == CallTraceEnum.Return:
            try:
                old_pc = ctx.trace.pop()
                log.debug(f'Leaving: \t{old_pc:#X}')
            except IndexError:
                log.debug(f'Negative stack pop or leaving entrypoint at {self.emu.pc:#X}')

    def _handle(self, obj):
        pass
