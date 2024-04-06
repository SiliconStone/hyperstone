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

    def _prepare(self):
        """
        Prepare for execution.
        """
        self.segment_plugin = Plugin.require(MapSegment, self.emu)
        self.write_plugin = Plugin.require(self.write_plugin_type, self.emu)

        self.segment_plugin.prepare(self.emu)

    def _handle(self, obj: RawSegment):
        """
        Raises:
            HSPluginInteractNotReadyError: _description_
        """
        if self.segment_plugin is None or self.write_plugin is None:
            raise HSPluginInteractNotReadyError(f'Could not require plugins! {self.segment_plugin=}, {self.write_plugin=}')

        if obj.stream.base is None:
            obj.stream.base = obj.segment.address

        self.segment_plugin.interact(obj.segment)
        self.write_plugin.interact(obj.stream)
