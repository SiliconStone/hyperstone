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
        Maps a single segment.

        Args:
            seg: The segment to map

        Raises:
            HSPluginInteractionError:
                if the segment has no size.
                Usually, this means an upper layer failed to infer the size of a segment.
        """
        if seg.size is None:
            log.error(f'Cannot infer Segment - {seg}\'s size!')
            raise HSPluginInteractionError(f'Segment {seg} has no size.')

        log.debug(f'Mapping segment {seg.name}: {seg}')
        self._segments.append(self.emu.mem.map(seg.address, seg.size, seg.name, seg.perms))
        self._mapped_info.append(seg)

    def __getitem__(self, name: str) -> SegmentInfo:
        """
        Gets a segment by name.

        Args:
            name: The name of the segment

        Returns:
            A SegmentInfo object that was used to map the segment.
            Note that this object is mutable, however changing it will have no effect.

        Raises:
            KeyError: The segment does not exist.
        """
        for seg in chain(self._mapped_info, self._interact_queue):
            if seg.name == name:
                return seg

        raise KeyError(f'Segment {name} not found')
