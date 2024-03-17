from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu

from hyperstone.exceptions import HSPluginInteractNotReadyError
from hyperstone.plugins.memory.map_segment import SegmentInfo
from hyperstone.plugins.memory.write_raw import WriteRaw, RawStream
from hyperstone.plugins.memory.map_segment import MapSegment

@dataclass
class RawSegment:
    stream: RawStream
    segment: SegmentInfo


class MapRaw(Plugin):
    """
    Map raw segment.
    """
    def __init__(self, *args: RawSegment):
        super().__init__(*args)
        self.segment_plugin: Optional[MapSegment] = None
        self.write_plugin: Optional[WriteRaw] = None
        self.write_plugin_type = WriteRaw

    def prepare(self, emu: HyperEmu):
        """
        Prepare for execution.

        Args:
            emu (HyperEmu): The emulator instance.
        """
        self.segment_plugin = self.require(MapSegment, emu)
        self.write_plugin = self.require(self.write_plugin_type, emu)

        self.segment_plugin.prepare(self.emu)

        super().prepare(emu)

    def _handle_interact(self, *objs: RawSegment):
        """
        Raises:
            HSPluginInteractNotReadyError: _description_
        """
        if self.segment_plugin is None or self.write_plugin is None:
            raise HSPluginInteractNotReadyError(f'Could not require plugins! {self.segment_plugin=}, {self.write_plugin=}')

        for obj in objs:
            if obj.stream.base is None:
                obj.stream.base = obj.segment.address

            self.segment_plugin.interact(obj.segment)
            self.write_plugin.interact(obj.stream)
