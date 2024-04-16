from typing import Optional

from hyperstone.plugins.memory.mappers.mem_setup import InitializeSupportStack
from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSHookBadParameters, HSHookBadState
from hyperstone.util.logger import log


def support_malloc(emu: HyperEmu, *, data: Optional[bytes] = None, size: Optional[int] = None) -> int:
    if data is None and size is None:
        raise HSHookBadParameters('You need to supply at least data or size!')
    if size is None:
        size = len(data)

    helper = Plugin.require(InitializeSupportStack, emu)
    helper.prepare(emu)

    if helper.support_free >= helper.support_segment.address + helper.support_segment.size:
        raise HSHookBadState('Not enough memory in support segment!')

    ptr = helper.support_free
    helper.support_free += size

    log.info(f'SUPPORT - allocated 0x{size:X} bytes at 0x{ptr:08X}')

    if data is not None:
        emu.mem.write(ptr, data)

    return ptr