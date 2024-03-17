from typing import Any

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu
from hyperstone.plugins.memory.map_segment import MapSegment
from hyperstone.plugins.memory.map_segment import SegmentInfo


class SetupMemory(Plugin):
    """
    Setup basic memory segements.
    E.g. stack and segment for internal use.
    """
    HYPERSTONE_SUPPORT_NAME = '_hyperstone_support'
    HYPERSTONE_STACK_NAME = 'stack'

    SUPPORT_BASE = 0x08000000
    SUPPORT_SIZE = 0x8000
    STACK_BASE = 0x7e000000
    STACK_SIZE = 0x8000

    def _handle_interact(self, *objs: Any):
        pass

    def __init__(self,
                 support_base: int = SUPPORT_BASE,
                 support_size: int = SUPPORT_SIZE,
                 stack_base: int = STACK_BASE,
                 stack_size: int = STACK_SIZE):
        super().__init__()
        self.support_segment = SegmentInfo(
            SetupMemory.HYPERSTONE_SUPPORT_NAME,
            support_base,
            support_size,
        )
        self.stack_segment = SegmentInfo(
            SetupMemory.HYPERSTONE_STACK_NAME,
            stack_base,
            stack_size,
        )

    def prepare(self, emu: HyperEmu):
        segments = self.require(MapSegment, emu)
        segments.interact(self.support_segment, self.stack_segment)
        super().prepare(emu)
