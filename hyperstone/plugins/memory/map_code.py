from dataclasses import dataclass

from hyperstone.plugins.memory.map_raw import MapRaw, RawSegment
from hyperstone.plugins.memory.map_segment import SegmentInfo
from hyperstone.plugins.memory.write_code import WriteCode, CodeStream


@dataclass
class CodeSegment(RawSegment):
    stream: CodeStream
    segment: SegmentInfo


class MapCode(MapRaw):
    """
    Map code segements.
    """
    def __init__(self, *args: CodeSegment):
        super().__init__(*args)
        self.write_plugin_type = WriteCode

