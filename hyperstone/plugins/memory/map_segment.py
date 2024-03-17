from dataclasses import dataclass

import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.util.logger import log

@dataclass
class SegmentInfo:
    name: str
    address: int
    size: int
    perms: ms.AccessType = ms.AccessType.RWX


class MapSegment(Plugin):
    """
    Map segment.
    """
    def __init__(self, *segments: SegmentInfo):
        super().__init__(*segments)
        self._segments = []

    def _handle_interact(self, *objs: SegmentInfo):
        """
        """
        for seg in objs:
            log.info(f'Mapping segment {seg.name}: {seg}')
            self._segments.append(self.emu.mem.map(seg.address, seg.size, seg.name, seg.perms))
