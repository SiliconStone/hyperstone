"""
ELF Loader
"""
import logging
from dataclasses import dataclass
from typing import Optional

import lief
from lief.ELF import E_TYPE
from lief.ELF import SEGMENT_TYPES
from lief.ELF import SEGMENT_FLAGS
import megastone as ms

from hyperstone import log
from hyperstone.exceptions import HSPluginInteractNotReadyError
from hyperstone.plugins.base import Plugin
from hyperstone.plugins.loaders.names import ELF_SEGMENT_NAME
from hyperstone.plugins.memory import RawStream
from hyperstone.plugins.memory.mappers.map_stream import (StreamMapper,
                                                          StreamMapperInfo)
from hyperstone.plugins.memory.mappers.map_segment import Segment, SegmentInfo


@dataclass(frozen=True)
class ELFInfo:
    path: str
    name: str
    base_address: int


def lief_perm_to_megastone(perm: SEGMENT_FLAGS) -> ms.AccessType:
    access = ms.AccessType.NONE
    if perm.R:
        access |= ms.AccessType.R
    if perm.W:
        access |= ms.AccessType.W
    if perm.X:
        access |= ms.AccessType.X
    return access


class ELFLoader(Plugin):
    _INTERACT_TYPE = ELFInfo

    def __init__(self, *files: ELFInfo):
        self._segment_plugin: Optional[Segment] = None
        self._stream_mapper: Optional[StreamMapper] = None
        super().__init__(*files)

    def _prepare(self):
        pass

    def _handle(self, obj: ELFInfo):
        binary: lief.ELF.Binary = lief.ELF.parse(obj.path)
        # Getting the e_type
        e_type = binary.header.file_type
        if e_type == E_TYPE.RELOCATABLE:
            # kernel object?
            pass
        if e_type == E_TYPE.DYNAMIC:
            # Shared object maybe load with ld?
            pass
        if e_type == E_TYPE.EXECUTABLE:
            # Executable
            self.load_executable(binary, elf=obj)

    def load_executable(self, binary: lief.ELF.Binary, elf: ELFInfo):
        """
        Load an ELF executable.

        Args:
            binary:

        Returns:

        """
        log.info(f"Loading {elf.name}")
        segments = [segment for segment in binary.segments
                    if segment.type == SEGMENT_TYPES.LOAD]
        segments = sorted(segments, key=lambda segment: segment.virtual_address)
        for seg in segments:
            self.mmap_segment(seg, elf=elf)

    def mmap_segment(self, segment: lief.ELF.Segment, elf: ELFInfo):
        if not self.ready:
            raise HSPluginInteractNotReadyError(f'ELF mapping: '
                                                f'0x{segment.virtual_address:016x}='
                                                f'0x{segment.virtual_size:08x}')
        self._stream_mapper.interact(
            StreamMapperInfo(
                stream=RawStream(segment.content.tobytes()),
                segment=SegmentInfo(
                    ELF_SEGMENT_NAME.format(file_name=elf.name,
                                            segment_name="no_name"),
                    elf.base_address + segment.virtual_address,
                    segment.virtual_size,
                    lief_perm_to_megastone(segment.flags),
                ),
            )
        )
