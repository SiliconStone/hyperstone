from dataclasses import dataclass
import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.plugins.hooks import Hooks, HookType
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSRuntimeBadAccess
from hyperstone.util.logger import log


@dataclass
class MemoryACL:
    range: ms.AddressRange
    access: ms.AccessType


class EnforceMemoryAccess(Plugin):
    def __init__(self, *ranges: MemoryACL):
        super().__init__(*ranges)
        self._hooks = []

        # Strict allow / deny for internal stuff
        self.allow = []
        self.deny = []

        # Plugins pushed overrides
        self.user = []

        # Base override / memory map
        self._base = []

        self._ranges = [self.allow, self.deny, self.user, self._base]

    def _prepare(self):
        hook_plugin: Hooks = Plugin.require(Hooks, self.emu)
        hook_plugin.prepare(self.emu)  # We need access to advanced API - add_hook()

        hook_plugin.add_hook(HookType('EnforceMemoryAccessHook', None, None), self._callback_access, ms.HookType.ACCESS)
        hook_plugin.add_hook(HookType('EnforceMemoryExecuteHook', None, None), self._callback_execute, ms.HookType.CODE)

    def _handle(self, obj: MemoryACL):
        self._base.append(obj)

    def _callback_access(self, emu: HyperEmu):
        self._access_check(emu, emu.curr_access.address, emu.curr_access.type)

    def _callback_execute(self, emu: HyperEmu):
        self._access_check(emu, emu.pc, ms.AccessType.X)

    def _access_check(self, emu: HyperEmu, address: int, access_type: ms.AccessType):
        for entry in self._ranges:
            for acl in entry:
                acl: MemoryACL
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