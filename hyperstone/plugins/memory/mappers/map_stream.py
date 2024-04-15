from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.memory.mappers.map_segment import SegmentInfo
from hyperstone.plugins.memory.writers.write_raw import RawStream
from hyperstone.plugins.memory.writers.write_stream import WriteStream, Stream
from hyperstone.plugins.memory.mappers.map_segment import MapSegment
from hyperstone.plugins.base import Plugin
from hyperstone.exceptions import HSPluginInteractNotReadyError
from hyperstone.util.logger import log


@dataclass
class StreamMappingInfo:
    stream: Stream
    segment: SegmentInfo


class MapStream(WriteStream):
    """
    Map and write a stream.
    """
    def __init__(self, *args: StreamMappingInfo):
        super().__init__(*args)
        self.segment_plugin: Optional[MapSegment] = None

    def _prepare(self):
        """
        Prepare for execution.
        """
        self.segment_plugin = Plugin.require(MapSegment, self.emu)
        self.segment_plugin.prepare(self.emu)

    def _handle(self, obj: StreamMappingInfo):
        """
        Raises:
            HSPluginInteractNotReadyError: _description_
        """
        if self.segment_plugin is None:
            raise HSPluginInteractNotReadyError(f'Could not require plugins! {self.segment_plugin=}')

        if obj.stream.base is None:
            obj.stream.base = obj.segment.address

        if obj.segment.size is None:
            log.debug(f'Attempting to get real size of {obj}')
            my_data = obj.stream.raw(self.emu)
            obj.segment.size = len(my_data)
            obj.stream = RawStream(my_data, obj.stream.base)

        self.segment_plugin.interact(obj.segment)
        super()._handle(obj.stream)
