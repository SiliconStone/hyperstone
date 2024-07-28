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
    """
    Represents a tuple of data and a segment.
    This object allows to map a segment and set its data at the same time.

    Attributes:
        stream:
            A data stream. Represents some data in some format.
        segment:
            The segment to be mapped, its size may be `None`, and if so, it'd be resolved to be the size of the
            stream
    """
    stream: Stream
    segment: SegmentInfo


class StreamMapper(StreamWriter):
    """
    Map and write a stream.
    """
    def __init__(self, *args: StreamMapperInfo):
        super().__init__(*args)
        self._segment_plugin: Optional[Segment] = None

    def _prepare(self):
        """
        Prepare for execution.
        """
        self._segment_plugin = Plugin.require(Segment, self.emu)
        self._segment_plugin.prepare(self.emu)

    def _handle(self, obj: StreamMapperInfo):
        """
        Raises:
            HSPluginInteractNotReadyError: In the undefined case of the plugin being called before being prepared
        """
        if self._segment_plugin is None:
            raise HSPluginInteractNotReadyError(f'Could not require plugins! {self._segment_plugin=}')

        if obj.stream.base is None:
            obj.stream.base = obj.segment.address

        my_data = obj.stream.raw(self.emu)
        if obj.segment.size is not None:
            my_data = my_data[:obj.segment.size]
        else:
            log.debug(f'Attempting to get real size of {obj}')
            obj.segment.size = len(my_data)
        obj.stream = RawStream(my_data, obj.stream.base)

        self._segment_plugin.interact(obj.segment)
        super()._handle(obj.stream)
