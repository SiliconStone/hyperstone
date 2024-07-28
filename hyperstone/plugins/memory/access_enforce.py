from dataclasses import dataclass
import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.plugins.hooks.base import Hook, HookInfo
from hyperstone.util.context import Context
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSRuntimeBadAccess
from hyperstone.util.logger import log


@dataclass
class EnforceMemoryInfo:
    """
    Represents a memory permission rule.

    Attributes:
        range: The memory to be affected by this rule
        access: The permission to be enforced upon this memory range
    """
    range: ms.AddressRange
    access: ms.AccessType


class EnforceMemory(Plugin):
    """
    This plugin allows advanced memory access rules.

    Due to the way that unicorn (and qemu) work, you may not have 2 close segments with different permissions in some
    architectures, this is due to how permissions are implemented on the hardware level.
    This plugin uses hooks to watch and enforce rules over the memory.
    Most plugins in hyperstone that support mapping memory with permissions support using this plugin if loaded,
    and will map the segment as RWX, while enforcing the permissions via this plugin.

    Notes:
        - This plugin uses Read, Write, and Code hooks and as such might slow down the emulator's speed. Note that
            unicorn is very, very slow with hooks and this is mostly a unicorn bottleneck.
        - As far as I know, there is no way (in python) to modify a mapped segment's permission (be it a megastone or
            unicorn limitation) as such, the only "accurate" way known to me to emulate `mprotect` is to use this plugin
            Note that you may also just map the `mprotect`'d memory as RWX from the start and just hook it / do other
            dirty tricks that might do the job.
        - This plugin offers a very basic priority system - user, allow, deny, base (interact()), where user overrides
            every other rules, (allow overrides deny, deny overrides base, allow overrides base, etc.). This system
            may be used as following: `user` for mprotect()s, `allow` and `deny` for malloc()s (allocating an "allowed"
            segment and surrounding it with "denied" rule to determine OOBs), free()s (using the previous example, just
            removing the `allow` rule, leaving only a deny rule for the entire memory range) and so on. Note that you
            may use these "layers" in any way.
        - In order to modify the other "layers" (allow, deny, user), you may access these attributes directly.
    """
    def __init__(self, *ranges: EnforceMemoryInfo):
        super().__init__(*ranges)
        self._hooks = []

        # Strict allow / deny for internal stuff
        self.allow = []
        self.deny = []

        # Plugins pushed overrides
        self.user = []

        # Base override / memory map
        self._base = []

        self._ranges = [self.user, self.allow, self.deny, self._base]

    def _prepare(self):
        hook_plugin: Hook = Plugin.require(Hook, self.emu)
        hook_plugin.prepare(self.emu)  # We need access to advanced API - add_hook()

        hook_plugin.add_hook(
            HookInfo('EnforceMemoryAccessHook', address=None, callback=self._callback_access, silent=True),
            ms.HookType.ACCESS
        )
        hook_plugin.add_hook(
            HookInfo('EnforceMemoryExecuteHook', address=None, callback=self._callback_execute, silent=True),
            ms.HookType.CODE
        )

    def _handle(self, obj: EnforceMemoryInfo):
        log.debug(f'Adding Rule - {obj}')
        self._base.append(obj)

    def _callback_access(self, ctx: Context):
        emu = ctx.emu
        self._access_check(emu, emu.curr_access.address, emu.curr_access.type)

    def _callback_execute(self, ctx: Context):
        emu = ctx.emu
        self._access_check(emu, emu.pc, ms.AccessType.X)

    def _access_check(self, emu: HyperEmu, address: int, access_type: ms.AccessType):
        for entry in self._ranges:
            for acl in entry:
                acl: EnforceMemoryInfo
                if not acl.range.contains(address):
                    continue

                if access_type & acl.access != access_type:
                    block = 'DENY' if entry == self.deny else None
                    block = 'ALLOW' if entry == self.allow else block
                    block = 'USER' if entry == self.user else block
                    block = 'BASE' if entry == self._base else block

                    error_msg = (f'Invalid access {access_type} for {address:08X}, '
                                 f'Denied by {acl} from block {block}')

                    log.error(error_msg)
                    emu.stop()
                    raise HSRuntimeBadAccess(error_msg)
                return
