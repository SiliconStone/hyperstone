from dataclasses import dataclass
from itertools import chain
from typing import Optional

import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.exceptions import HSPluginInteractionError
from hyperstone.util.resolver import LazyResolver
from hyperstone.util.logger import log


@dataclass
class SegmentInfo:
    name: str
    address: int
    size: Optional[int] = None
    perms: ms.AccessType = ms.AccessType.RWX


class Segment(Plugin):
    """
    Map segment.
    """
    def __init__(self, *segments: SegmentInfo):
        super().__init__(*segments)
        self._mapped_info = []
        self._segments = []

    def _handle(self, seg: SegmentInfo):
        """
        """
        if seg.size is None:
            log.error(f'Cannot infer Segment - {seg}\'s size!')
            raise HSPluginInteractionError(f'Segment {seg} has no size.')

        log.info(f'Mapping segment {seg.name}: {seg}')
        self._segments.append(self.emu.mem.map(seg.address, seg.size, seg.name, seg.perms))
        self._mapped_info.append(seg)

    def __getitem__(self, name: str) -> SegmentInfo:
        for seg in chain(self._mapped_info, self._interact_queue):
            if seg.name == name:
                return seg

        raise KeyError(f'Segment {name} not found')

    def __matmul__(self, other: str) -> LazyResolver:
        return LazyResolver(self)[other]
