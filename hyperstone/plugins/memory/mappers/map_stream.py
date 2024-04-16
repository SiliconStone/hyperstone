from dataclasses import dataclass
from typing import Optional

from hyperstone.plugins.memory.mappers.map_segment import SegmentInfo
from hyperstone.plugins.memory.streams.stream import Stream
from hyperstone.plugins.memory.streams.write_raw import RawStream
from hyperstone.plugins.memory.streams.write_stream import StreamWriter
from hyperstone.plugins.memory.mappers.map_segment import Segment
from hyperstone.plugins.base import Plugin
from hyperstone.exceptions import HSPluginInteractNotReadyError
from hyperstone.util.logger import log


@dataclass
class StreamMapperInfo:
    stream: Stream
    segment: SegmentInfo


class StreamMapper(StreamWriter):
    """
    Map and write a stream.
    """
    def __init__(self, *args: StreamMapperInfo):
        super().__init__(*args)
        self.segment_plugin: Optional[Segment] = None

    def _prepare(self):
        """
        Prepare for execution.
        """
        self.segment_plugin = Plugin.require(Segment, self.emu)
        self.segment_plugin.prepare(self.emu)

    def _handle(self, obj: StreamMapperInfo):
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
