from dataclasses import dataclass
import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.plugins.hooks.base import Hook, HookInfo
from hyperstone.plugins.hooks.context import Context
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSRuntimeBadAccess
from hyperstone.util.logger import log


@dataclass
class EnforceMemoryInfo:
    range: ms.AddressRange
    access: ms.AccessType


class EnforceMemory(Plugin):
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

        hook_plugin.add_hook(HookInfo('EnforceMemoryAccessHook', None, callback=self._callback_access), ms.HookType.ACCESS)
        hook_plugin.add_hook(HookInfo('EnforceMemoryExecuteHook', None, callback=self._callback_execute), ms.HookType.CODE)

    def _handle(self, obj: EnforceMemoryInfo):
        log.debug(f'Adding ACL - {obj}')
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
