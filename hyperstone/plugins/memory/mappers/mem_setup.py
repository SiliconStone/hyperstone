from typing import Any

from hyperstone.plugins.memory.mappers.map_segment import Segment, SegmentInfo
from hyperstone.plugins.base import Plugin


class InitializeSupportStack(Plugin):
    """
    This plugin sets up some basic and useful hyperstone (and megastone) segments.
    You most likely will always need this plugin in your project.

    Segments that are mapped:
        stack:
            A stack segment that is `megastone` compatible, this plugin also sets the `sp` register of the emulator
            To point at the top of the stack (minus the `STACK_BACKPADDLE` amount).
            A `megastone` compliant segment allows to use the `emu.stack` API
        [hyperstone heap]:
            Internal hyperstone "heap", usually not used by most programs. Maps a memory segment that allows the user
            to allocate mock objects, see `support_malloc()`

    Notes:
        The primary reason this crucial plugin is implemented as a plugin and not as a builtin feature is to keep
        the hyperstone engine as minimal and modular as possible. A pure hyperstone emulator instance without any
        plugins should be as close to a pure just-made megastone / unicorn emulator instance. (except for some utility
        objects such as the global context)
    """
    HYPERSTONE_SUPPORT_NAME = '[hyperstone heap]'
    HYPERSTONE_STACK_NAME = 'stack'

    SUPPORT_BASE = 0x80000000
    SUPPORT_SIZE = 0x8000
    STACK_BASE = 0x7e000000
    STACK_SIZE = 0x8000
    STACK_BACKPADDLE = 0x100

    def _handle(self, obj: Any):
        pass

    def __init__(self,
                 support_base: int = SUPPORT_BASE,
                 support_size: int = SUPPORT_SIZE,
                 stack_base: int = STACK_BASE,
                 stack_size: int = STACK_SIZE,
                 stack_backpaddle: int = STACK_BACKPADDLE):
        super().__init__()
        self.support_segment = SegmentInfo(
            InitializeSupportStack.HYPERSTONE_SUPPORT_NAME,
            support_base,
            support_size,
        )
        self.stack_segment = SegmentInfo(
            InitializeSupportStack.HYPERSTONE_STACK_NAME,
            stack_base,
            stack_size,
        )
        self.support_free = None
        self.stack_backpaddle = stack_backpaddle

    def _prepare(self):
        segments = Plugin.require(Segment, self.emu)

        segments.prepare(self.emu)  # We need it instantly in order to init the sp for megastone
        segments.interact(self.support_segment, self.stack_segment)

        self.support_free = self.support_segment.address
        self.emu.reset_sp()
        self.emu.sp -= self.stack_backpaddle
