from abc import ABC
from dataclasses import dataclass
from typing import Any, Optional

import megastone as ms
import hyperstone as hs
from hyperstone import HyperEmu


class Entrypoint(hs.RunnerPlugin, ABC):
    def __init__(self, entrypoint: int):
        super().__init__()
        self.entrypoint = entrypoint

    def _run(self):
        try:
            self.emu.run_function(self.entrypoint)
        except ms.MemFaultError as f:
            hs.log.error(f)


@dataclass
class SegmentDecl:
    name: str
    address: int
    size: int
    perms: ms.AccessType = ms.AccessType.RWX


class SegmentPlugin(hs.Plugin):
    def __init__(self, *segments: SegmentDecl):
        super().__init__()
        self.interact_queue += segments

    def _handle_interact(self, *objs: SegmentDecl):
        for seg in objs:
            hs.log.info(f'Mapping segment {seg.name}: {seg}')
            self.emu.mem.map(seg.address, seg.size, seg.name, seg.perms)


class SetupMemory(hs.Plugin):
    def _handle_interact(self, *objs: Optional[Any]):
        pass

    SUPPORT_BASE = 0x08000000
    SUPPORT_SIZE = 0x8000
    STACK_BASE = 0x7e000000
    STACK_SIZE = 0x8000

    def __init__(self, *,
                 support_base: int = SUPPORT_BASE,
                 support_size: int = SUPPORT_SIZE,
                 stack_base: int = STACK_BASE,
                 stack_size: int = STACK_SIZE):
        super().__init__()
        self.support_segment = SegmentDecl(
            'hyperstone_support',
            support_base,
            support_size,
        )
        self.stack_segment = SegmentDecl(
            'stack',
            stack_base,
            stack_size,
        )

    def prepare(self, emu: HyperEmu):
        segments = self.require(SegmentPlugin, emu)
        segments.interact(self.support_segment, self.stack_segment)
        super().prepare(emu)


class Settings(hs.Settings):
    DEFAULT_SEGMENTS = SetupMemory()

    SEGMENTS = SegmentPlugin(
        SegmentDecl(
            'test1',
            0x40000000,
            0x1000,
        ),
        SegmentDecl(
            'test2',
            0x41000000,
            0x1000,
            ms.AccessType.RX
        )
    )

    ENTRY = Entrypoint(0x40000000)


SIMPLE_SETTINGS = [
    SetupMemory(),

    SegmentPlugin(
        SegmentDecl(
            'test1',
            0x40000000,
            0x1000,
        ),
        SegmentDecl(
            'test2',
            0x41000000,
            0x1000,
            ms.AccessType.RX
        )
    ),

    Entrypoint(0x40000000),
]


if __name__ == '__main__':
    hs.start(ms.ARCH_ARM, SIMPLE_SETTINGS)
