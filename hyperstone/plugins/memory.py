from dataclasses import dataclass
from typing import Optional, Any

import megastone as ms

from hyperstone.errors.plugins import HSPluginInteractNotReady
from hyperstone.emulator import HyperEmu
from hyperstone.plugins.base import Plugin
from hyperstone.util import log


@dataclass
class SegmentDecl:
    name: str
    address: int
    size: int
    perms: ms.AccessType = ms.AccessType.RWX


@dataclass
class CodeStream:
    assembly: str
    base: Optional[int] = None
    isa: Optional[ms.InstructionSet] = None


@dataclass
class RawStream:
    data: bytes
    base: Optional[int] = None


@dataclass
class CodeSegment:
    stream: CodeStream
    segment: SegmentDecl


@dataclass
class RawSegment:
    stream: RawStream
    segment: SegmentDecl


class MapSegment(Plugin):
    def __init__(self, *segments: SegmentDecl):
        super().__init__()
        self._interact_queue += segments

    def _handle_interact(self, *objs: SegmentDecl):
        for seg in objs:
            log.info(f'Mapping segment {seg.name}: {seg}')
            self.emu.mem.map(seg.address, seg.size, seg.name, seg.perms)


class SetupMemory(Plugin):
    HYPERSTONE_SUPPORT_NAME = '_hyperstone_support'
    HYPERSTONE_STACK_NAME = 'stack'

    SUPPORT_BASE = 0x08000000
    SUPPORT_SIZE = 0x8000
    STACK_BASE = 0x7e000000
    STACK_SIZE = 0x8000

    def _handle_interact(self, *objs: Any):
        pass

    def __init__(self, *,
                 support_base: int = SUPPORT_BASE,
                 support_size: int = SUPPORT_SIZE,
                 stack_base: int = STACK_BASE,
                 stack_size: int = STACK_SIZE):
        super().__init__()
        self.support_segment = SegmentDecl(
            SetupMemory.HYPERSTONE_SUPPORT_NAME,
            support_base,
            support_size,
        )
        self.stack_segment = SegmentDecl(
            SetupMemory.HYPERSTONE_STACK_NAME,
            stack_base,
            stack_size,
        )

    def prepare(self, emu: HyperEmu):
        segments = self.require(MapSegment, emu)
        segments.interact(self.support_segment, self.stack_segment)
        super().prepare(emu)


class WriteRaw(Plugin):
    def __init__(self, *args: RawStream):
        super().__init__()
        self._interact_queue += args

    def _handle_interact(self, *objs: RawStream):
        for obj in objs:
            if obj.base is None:
                raise ValueError(f'Cannot infer base address for {obj}')
            self.emu.mem.write(obj.base, obj.data)
            log.info(f'Wrote {len(obj.data):08X} bytes to {obj.base:08X}...')


class MapRaw(Plugin):
    def __init__(self, *args: RawSegment):
        super().__init__()
        self._interact_queue += args
        self.segment_plugin: Optional[MapSegment] = None
        self.write_plugin: Optional[WriteRaw] = None
        self.write_plugin_type = WriteRaw

    def prepare(self, emu: HyperEmu):
        self.segment_plugin = self.require(MapSegment, emu)
        self.write_plugin = self.require(self.write_plugin_type, emu)

        self.segment_plugin.prepare(self.emu)

        super().prepare(emu)

    def _handle_interact(self, *objs: RawSegment):
        if self.segment_plugin is None or self.write_plugin is None:
            raise HSPluginInteractNotReady(f'Could not require plugins! {self.segment_plugin=}, {self.write_plugin=}')

        for obj in objs:
            if obj.stream.base is None:
                obj.stream.base = obj.segment.address

            self.segment_plugin.interact(obj.segment)
            self.write_plugin.interact(obj.stream)


class WriteCode(Plugin):
    def __init__(self, *args: CodeStream):
        super().__init__()
        self._interact_queue += args

    def _handle_interact(self, *objs: CodeStream):
        for obj in objs:
            if obj.base is None:
                raise ValueError(f'Cannot infer base address for {obj}')
            write_size = self.emu.mem.write_code(obj.base, obj.assembly, obj.isa)
            log.info(f'Wrote {write_size:08X} bytes to {obj.base:08X}...')


class MapCode(MapRaw):
    def __init__(self, *args: CodeSegment):
        super().__init__(*args)
        self.write_plugin_type = WriteCode
