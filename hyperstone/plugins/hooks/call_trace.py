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
        """
        This function resets the context state
        """
        self.last_pc = None
        self.pc = None
        self.trace.clear()
        self._l1_cache.clear()
        self._l2_cache.clear()

    def _check_call_slow(self) -> CallTraceEnum:
        """
        This function does a more accurate check for the opcode
        If it runs the same address multiple times (set by l2_cache_sensitivity), then it returns the cached result
        Otherwise, we check the bytes themselves against our cache
        If the opcode wasn't in our cache, then we use megastone (via capstone's modules) to actually check the opcode

        Returns:
            `CallTraceEnum.Call` - if the opcode executes a "call" like action
            `CallTraceEnum.Return` - if the opcode executes a "return" like action
            `CallTraceEnum.Normal` - for any other opcode
        """
        insn_addr = EmuAddress(self.last_pc)

        if insn_addr in self._l2_cache:
            return self._l2_cache[insn_addr].value

        opcode = EmuOpcode(self.emu.mem.read(self.last_pc, self.l1_cache_sensitivity))
        if opcode in self._l1_cache:
            cache = self._l1_cache[opcode]
            cache.hits += 1
            if cache.hits > self.l2_cache_sensitivity != 0:
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
        """
        This function does a simple check of the opcode
        If the next opcode is not far enough from the last opcode, then we assume no jump-like opcode has been executed
        Otherwise, we use more accurate checks for the opcode

        You may disable this assumption by setting `sensitivity` to 0

        Returns:
            `CallTraceEnum.Call` - if the opcode executes a "call" like action
            `CallTraceEnum.Return` - if the opcode executes a "return" like action
            `CallTraceEnum.Normal` - for any other opcode
        """
        if self.last_pc is None or self.pc is None:
            return CallTraceEnum.Normal
        if self.emu is None:
            return CallTraceEnum.Normal

        if abs(self.pc - self.last_pc) < self.sensitivity != 0:
            # Too low for a call
            return CallTraceEnum.Normal

        return self._check_call_slow()

    def next(self) -> CallTraceEnum:
        """
        Update the `pc` and check the last executed opcode.

        Returns:
            `CallTraceEnum.Call` - if the opcode executes a "call" like action
            `CallTraceEnum.Return` - if the opcode executes a "return" like action
            `CallTraceEnum.Normal` - for any other opcode
        """
        self.last_pc = self.pc
        self.pc = self.emu.pc

        return self._check_call()


class CallTrace(Plugin):
    """
    This plugin logs almost-every call and return action that was executed by the emulator.
    Note that this plugin sets a hook for every CODE action (every opcode), which is very slow in `unicorn` (the library
    that hyperstone and megastone are using)
    """
    def __init__(self, sensitivity: int = 8):
        self._hook: Optional[ActiveHook] = None
        self._hook_plugin: Optional[Hook] = None
        self._sensitivity = sensitivity
        self.trace = []
        log.warning('This plugin is fairly slow (and spammy). It adds a global code Hook which chokes on Unicorn\'s '
                    'internal code hook handler and register read handler. Use with caution!')
        super().__init__()

    def _prepare(self):
        self._hook_plugin = Plugin.require(Hook, self.emu)
        self._hook_plugin.prepare(self.emu)

        ctx = CallTraceContext(self._sensitivity)
        ctx.trace = self.trace  # Hooking by-ref into the trace

        self._hook = self._hook_plugin.add_hook(
            HookInfo(
                name='_CallTraceHook',
                address=None,
                callback=self._callback,
                ctx=ctx,
            ),
            ms.HookType.CODE
        )
        self._hook.info.ctx.hook = self._hook
        self._hook.info.ctx.emu = self.emu

    def pop(self):
        """
        This function forces a "pop" of our current stack, forcing a fake "return" opcode
        This might be used by other hooks to better keep track of calls and returns
        """
        if self._hook is None:
            raise HSPluginBadStateError('Cannot pop without installing hook first')

        self._handle_call_type(CallTraceEnum.Return)

    def _callback(self, ctx: CallTraceContext):
        call_type = ctx.next()
        self._handle_call_type(ctx, call_type)

    def _handle_call_type(self, ctx: CallTraceContext, call_type: CallTraceEnum):
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
